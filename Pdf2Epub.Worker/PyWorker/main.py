from typing import Any, Callable, Generic, Iterable, Iterator, Literal, TypeVar
from dataclasses import dataclass
import numpy as np
import unicodedata
import html
import math
import base64
import lzma
import pickle

import fitz

from line import Line, LineType, make_line, line_type
import utils
import epubgen

# import nltk
# nltk.download('words')
# from nltk.corpus import words

T = TypeVar('T')
JsonLike = dict[str, Any]
Block = JsonLike
Span = JsonLike
BlockIter = Iterator[Block]

LineIter = Iterator[Line]
SpanIter = Iterator[Span]
BBox = tuple[float, float, float, float]
FontFlags = tuple[int, int]


@dataclass
class ConvertOptions:
    vertical: bool


@utils.curry_first_arg
def open_pdf(opt: ConvertOptions, src: str) -> fitz.Document:
    """Open a PDF file using PyMuPDF."""

    def merge_by_first(arr: Iterable[tuple[float, int]]) \
            -> list[tuple[float, int]]:
        dic = {}
        for k, v in arr:
            if k in dic:
                dic[k] += v
            else:
                dic[k] = v
        return [(k, v) for k, v in dic.items()]

    def significant(arr: list[float]) -> int:
        assert len(arr) > 0
        bound = arr[0] * 0.2
        for i in range(1, len(arr)):
            if arr[i] < bound:
                return i
        return len(arr)

    def analyze(page: fitz.Page) -> Iterator[Any]:
        rect = page.rect
        dic = page.get_text('dict')
        blks = dic['blocks']
        for blk in blks:
            assert ('lines' in blk) or ('image' in blk)
            if 'lines' in blk:
                l, u, r, d = blk['bbox']
                n_line = len(blk['lines'])
                n_char = 0
                text_sizes = []
                for line in blk['lines']:
                    text = ''
                    for span in line['spans']:
                        text += span['text']
                        text_sizes.append((span['size'], len(span['text'])))
                    n_char += len(text)
                text_sizes = merge_by_first(text_sizes)
                yield 'text', blk['bbox'], (n_line, n_char), text_sizes
            if 'image' in blk:
                yield 'image', blk['bbox']

    doc = fitz.open(src)
    toc = doc.get_toc()
    metadata = doc.metadata
    pages = list(doc.pages())
    text_sizes = []
    for page in pages:
        for _, _, sizes in analyze(page):
            text_sizes.extend(sizes)
    text_sizes = merge_by_first(text_sizes)
    text_sizes.sort(key=lambda x: x[1], reverse=True)
    # print(*text_sizes, sep='\n')

    return doc


def extract_toc(src: str) -> list:
    doc = fitz.open(src)
    toc = doc.get_toc()
    return [(t[0], t[1]) for t in toc]


def extract_title(src: str) -> list:
    doc = fitz.open(src)
    metadata = doc.metadata
    title = 'PDF2ePub' if 'title' not in metadata or metadata['title'] == '' else metadata['title']
    return title


@utils.curry_first_arg
def extract_rawlines(opt: ConvertOptions, src: str) -> LineIter:
    """Returns a text block iterator of a PDF file."""

    doc = fitz.open(src)
    for page in doc.pages():
        dic = page.get_text('dict')
        for blk in dic['blocks']:
            assert 'lines' in blk or 'image' in blk
            if 'lines' in blk:
                for line in blk['lines']:
                    line['page'] = page.number
                    yield make_line(line, LineType.TEXT)
            if 'image' in blk:
                blk['page'] = page.number
                yield make_line(blk, LineType.IMAGE)


def merge_bboxes(b1: BBox, b2: BBox) -> BBox:
    """Merge two bounding boxes."""

    return min(b1[0], b2[0]), min(b1[1], b2[1]), \
           max(b1[2], b2[2]), max(b1[3], b2[3])


def merge_lines(l1: Line, l2: Line) -> Line:
    """Merge two lines."""

    line = l1.copy()
    last_span = line['spans'][-1]
    curr_span = l2['spans'][0]
    if span_equal_up_to_props(last_span, curr_span):
        new_span = merge_spans(last_span, curr_span)
        line['spans'][-1] = new_span
        line['spans'].extend(l2['spans'][1:])
    else:
        line['spans'].extend(l2['spans'])
    line['bbox'] = merge_bboxes(line['bbox'], l2['bbox'])
    return line


def span_equal_up_to_props(s1: Span, s2: Span) -> bool:
    """Whether two spans have same properties."""

    return len(s1['text']) == 0 or len(s2['text']) == 0 \
           or (s1['size'] == s2['size']
               and s1['flags'] == s2['flags']
               and s1['color'] == s2['color'])


def fix_whitespace(prev_text: str, text: str) -> str:
    """Add a space when it's appropriate."""

    prev_text = prev_text.rstrip()
    if len(prev_text) == 0:
        return text
    prev_char = prev_text[-1]
    if unicodedata.east_asian_width(prev_char) in ('F', 'W', 'A') \
            or prev_char.isspace() \
            or prev_char in '-' \
            or '://' in prev_text:
        return text.lstrip()
    return ' ' + text.lstrip()


with lzma.open('words.xz', 'rb') as f:
    english_words_ = pickle.load(f)


def is_english_word(word: str) -> bool:
    """Check whether a string is a word in English."""

    return word in english_words_ \
           or len(word) > 1 and word[:-1] in english_words_ \
           or len(word) > 2 and word[:-2] in english_words_ \
           or len(word) > 3 and word[:-3] in english_words_ \
           or word.replace('ing', 'e') in english_words_ \
           or word.replace('ion', 'e') in english_words_ \
           or word.replace('ied', 'y') in english_words_ \
           or word.replace('ies', 'y') in english_words_


def merge_texts(t1: str, t2: str) -> str:
    """Merges two pieces of text.

    Remove hyphens when appropriate."""

    if len(t1) >= 2 and t1[-1] == '-' and t1[-2].isalpha():
        t1 = t1[:-1]
        i, j = -1, 0
        while -i <= len(t1) and t1[i].isalpha():
            i -= 1
        while j < len(t2) and t2[j].isalpha():
            j += 1
        ll, lr, rl, rr = t1[:i + 1], t1[i + 1:], t2[:j], t2[j:]
        word = lr + rl
        if is_english_word(word.upper().lower()):
            return ll + word + rr
        else:
            return ll + lr + '-' + rl + rr
    return t1 + fix_whitespace(t1, t2)


def merge_spans(s1: Span, s2: Span) -> Span:
    """Merge text of two spans and fix whitespace."""

    span = s1.copy()
    if len(span['text']) == 0:
        span['text'] = s2['text']
    if len(s2['text']) > 0:
        span['text'] = merge_texts(span['text'], s2['text'])
    span['bbox'] = merge_bboxes(span['bbox'], s2['bbox'])
    return span


def line_bbox(line: Line) -> BBox:
    """Gets the bounding box of a line by merging span bounding boxes."""

    bbox = (float('+inf'), float('+inf'), float('-inf'), float('-inf'))
    for span in line['spans']:
        bbox = merge_bboxes(bbox, span['bbox'])
    return bbox


def splice_horizontal_rawlines(lines: LineIter) -> LineIter:
    """Splice spans that are of the same horizontal height but were misplaced
    into separate lines back into the same line."""

    def within_vertical_span(bbox: BBox, span: Span) -> bool:
        """Whether a span is ``within'' the vertical span of a bounding
        box."""

        ml, mu, mr, md = bbox
        l, u, r, d = span['bbox']
        return mu < (u + d) / 2 < md

    last_line = None
    for line in lines:
        if last_line is None:
            last_line = line
            continue
        # Do case analysis on the type tags of (last_line, line)
        ts = (line_type(last_line), line_type(line))
        if ts == (LineType.TEXT, LineType.TEXT):
            pred = lambda s: within_vertical_span(last_line['bbox'], s)
            t, f = utils.split_on(pred, line['spans'])
            # Add a space when appropriate
            if len(t) > 0 and len(last_line['spans']) > 0:
                prev_text = last_line['spans'][-1]['text']
                t[0]['text'] = fix_whitespace(prev_text, t[0]['text'])
            last_line['spans'].extend(t)
            # Don't stream the current line if it belongs to the last line
            if len(f) == 0:
                continue
            line['spans'] = f
            # Re-calculate line bounding box after modifying its spans
            last_line['bbox'] = line_bbox(last_line)
            line['bbox'] = line_bbox(line)
        yield last_line
        last_line = line
    t = line_type(last_line)
    if t == LineType.TEXT:
        if len(last_line['spans']) > 0:
            yield last_line
    elif t == LineType.IMAGE:
        yield last_line


def splice_vertical_rawlines(lines: LineIter) -> LineIter:
    """Splice extracted lines into literal lines for documents that are
    vertically typesetted."""

    def should_splice(last_line: Line, line: Line) -> bool:
        """Whether current line should belong to the last line.

        Returns True if the bounding box of the first span of the new line is
        below the bounding box of the last span of the last line, by comparing
        the horizontal height of the mid-point of the bounding boxes."""

        if len(last_line['spans']) == 0 or len(line['spans']) == 0:
            return True
        _, pu, _, pd = last_line['spans'][-1]['bbox']
        _, cu, _, cd = line['spans'][-1]['bbox']
        return cu + cd > pu + pd

    last_line = None
    for line in lines:
        if last_line is None:
            last_line = line
            continue
        # Do case analysis on the type tags of (last_line, line)
        ts = (line_type(last_line), line_type(line))
        if ts == (LineType.TEXT, LineType.TEXT):
            if should_splice(last_line, line):
                last_line['spans'].extend(line['spans'])
                continue
        last_line['bbox'] = line_bbox(last_line)
        yield last_line
        last_line = line
    last_line['bbox'] = line_bbox(last_line)
    yield last_line


def splice_rawlines(opt: ConvertOptions) -> Callable[[LineIter], LineIter]:
    """Decide which procedure to use based on whether the document is
    vertically typesetted."""

    return splice_vertical_rawlines \
        if opt.vertical \
        else splice_horizontal_rawlines


@utils.curry_first_arg
def reformat_rawlines(opt: ConvertOptions, lines: LineIter) -> LineIter:
    """Rectify and simplify spans, merge spans that have same properties,
    remove unused properties from lines."""

    def reformat_text_line_span(span: Span) -> Span:
        """Reformat font flags and font color of a span."""

        def reformat_flags(flags: int) -> FontFlags:
            """Make font flags more readable.

            Returns a tuple (cate, fl) where cate is 0, 1 or 2 representing
            serif, sans-serif or monospace and fl is a binary flag whose bits
            represent superscript, italic and bold respectively (from the
            lowest bit)."""

            if flags & 1 << 3:
                cate = 2  # monospace
            elif flags & 1 << 2:
                cate = 0  # serif
            else:
                cate = 1  # sans-serif
            fl = 0
            fl |= (flags & 1 << 0) >> 0  # superscript
            fl |= (flags & 1 << 1) >> 0  # italic
            fl |= (flags & 1 << 4) >> 2  # bold
            return cate, fl

        def reformat_color(color: int) -> str:
            """Make font color more readable."""

            return '#' + hex(color)[2:].zfill(6)

        span['flags'] = reformat_flags(span['flags'])
        span['color'] = reformat_color(span['color'])
        return span

    def simplify_text_line_span(span: Span) -> Span:
        """Remove unused properties from a text line span."""

        props = ['size', 'flags', 'color', 'text', 'bbox']
        return utils.filter_dict_by(props, span)

    def simplify_text_line(line: Line) -> Line:
        """Remove unused properties from a text line."""

        props = ['spans', 'bbox', 'page']
        line = utils.filter_dict_by(props, line)
        return make_line(line, LineType.TEXT)

    def merge_spans_of_a_text_line(line: Line) -> Line:
        """Merge spans of a text line that have same properties."""

        spans = []
        last_span = None
        for span in line['spans']:
            if last_span is None:
                last_span = span
                continue
            if span_equal_up_to_props(last_span, span):
                last_span = merge_spans(last_span, span)
            else:
                spans.append(last_span)
                last_span = span
        spans.append(last_span)
        line['spans'] = spans
        return line

    def span_level(process: Callable[[Span], Span]) \
            -> Callable[[Line], Line]:
        """Apply a processor (function) to all spans in a line."""

        def line_processor(line: Line) -> Line:
            line['spans'] = [process(span) for span in line['spans']]
            return line

        return line_processor

    text_line_steps = [
        span_level(reformat_text_line_span),
        span_level(simplify_text_line_span),
        simplify_text_line,
        merge_spans_of_a_text_line
    ]
    for line in lines:
        t = line_type(line)
        if t == LineType.TEXT:
            for step_fn in text_line_steps:
                line = step_fn(line)
            yield line
        elif t == LineType.IMAGE:
            yield line


@utils.curry_first_arg
def aggregate_lines(opt: ConvertOptions, lines: LineIter) -> LineIter:
    """Aggregate lines into paragraphs."""

    def is_eos(text: str) -> bool:
        """Whether a piece of text is at the end of a sentence."""

        stripped = text.strip()
        if len(stripped) == 0:
            return False
        eos = stripped[-1] in '。.！!？?”"…'
        # Example: https://example.com
        url = stripped[-1] == '.' \
              and '://' in stripped
        # Example: Donald E. Knuth
        nym = len(stripped) >= 2 \
              and stripped[-1] == '.' \
              and stripped[-2].isupper()
        # Example: i.e., e.g., s.t.
        lat = len(stripped) >= 4 \
              and stripped[-1] == '.' \
              and stripped[-3] == '.'
        return eos and not (url or nym or lat)

    def line_text(line: Line) -> str:
        """Concatenate pieces of text within a line into one."""

        return ''.join(span['text'] for span in line['spans'])

    def tagged(lines: LineIter) -> Iterator[tuple[Line, bool]]:
        """Analyze lines and return a tuple for each line containing the line
        itself and a tag indicating whether it should belong to the previous
        line."""

        def get_lurd(line: Line) -> tuple[float, float, float, float]:
            """Get the beginning position (L) and ending position (R) of a
            line based on its bounding box and whether the document is
            vertically typesetted."""

            if opt.vertical:
                u, l, d, r = line['bbox']
            else:
                l, u, r, d = line['bbox']
            return l, u, r, d

        def column_lrs(lrs: list[tuple[float, float]]) \
                -> list[tuple[float, float]]:
            if len(lrs) == 0:
                return []
            cnt = []

            def inc(l: int, r: int) -> None:
                if r >= len(cnt):
                    cnt.extend([0] * (r + 1 - len(cnt)))
                for i in range(l, r + 1):
                    cnt[i] += 1

            def cluster(lst: list[int]) -> list[int]:
                res = []
                left, last = -100, -100
                for x in lst + [-1]:
                    if x == last + 1:
                        last = x
                    else:
                        res.append(round((left + last) / 2))
                        left, last = x, x
                return res[1:]

            for l, r in lrs:
                inc(math.ceil(l), math.floor(r))
            lb = max(cnt) * 0.3
            delim = cluster([c for c in range(len(cnt)) if cnt[c] < lb])
            if cnt[-1] >= lb:
                delim.append(len(cnt) + 10)
            delim = list(map(float, delim))
            delim = list(zip(delim[:-1], delim[1:]))
            return delim

        def within_column(col: tuple[float, float],
                          lr: tuple[float, float]) -> bool:
            lm, rm = col
            ran = rm - lm
            k = 0.05
            l, r = lr
            return lm - k * ran < l and r < rm + k * ran

        def column_bounds(col: tuple[float, float],
                          ls: list[float],
                          rs: list[float]) -> tuple[float, float]:

            def bounds(arr: list[float]) -> tuple[float, float]:
                arr = np.array(arr)
                mean = arr.mean()
                var = math.sqrt(((arr - mean) ** 2).mean())
                lb = mean - 1.96 * var
                ub = mean + 1.96 * var
                return lb, ub

            pred = utils.curry_first_arg(within_column)(col)
            ls, rs = zip(*filter(pred, zip(ls, rs)))
            l_lb, l_ub = bounds(ls)
            r_lb, r_ub = bounds(rs)
            return l_ub, r_lb

        def columns_and_bounds(ls: list[float], rs: list[float]) \
                -> list[tuple[tuple[float, float], tuple[float, float]]]:
            cols = column_lrs([(l, r) for l, r in zip(ls, rs)])
            bds = [column_bounds(col, ls, rs) for col in cols]
            return list(zip(cols, bds))

        def columns_and_bounds_for_text_lines(lines: list[Line]) \
                -> list[tuple[tuple[float, float], tuple[float, float]]]:
            ls, rs = [], []
            for line in lines:
                t = line_type(line)
                if t != LineType.TEXT:
                    continue
                l, _, r, _ = get_lurd(line)
                text = line_text(line)
                if not is_eos(text):
                    ls.append(l)
                    rs.append(r)
            return columns_and_bounds(ls, rs)

        lines = list(lines)
        pred = lambda line: line['page'] % 2 == 0
        odd_page_lines, even_page_lines = utils.split_on(pred, lines)
        odd_col_bd = columns_and_bounds_for_text_lines(odd_page_lines)
        even_col_bd = columns_and_bounds_for_text_lines(even_page_lines)

        def is_eoc(line: Line) -> bool:
            """Whether a right side of a line is at the end of a column."""

            l, _, r, _ = get_lurd(line)
            col_bd = odd_col_bd if pred(line) else even_col_bd
            for col, bd in col_bd:
                if within_column(col, (l, r)):
                    _, rb = bd
                    return r > rb
            return False

        def is_title(line: Line) -> bool:
            t = line_type(line)
            if t != LineType.TEXT:
                return False
            text = line_text(line)
            if any(c in text for c in '，。,'):
                return False
            # print(text)
            return False

        sm = [False]
        for line, next_line in zip(lines[:-1], lines[1:]):
            t = line_type(line)
            if t == LineType.TEXT:
                _, u, r, d = get_lurd(line)
                # _, u_next, _, d_next = get_lurd(next_line)
                is_title(line)
                line_sm = not is_eos(line_text(line)) \
                          and is_eoc(line)
                sm.append(line_sm)
            elif t == LineType.IMAGE:
                sm.append(False)
        return zip(lines, sm)

    last_line = None
    for line, should_merge in tagged(lines):
        if last_line is None:
            last_line = line
            continue
        t = (line_type(last_line), line_type(line))
        if should_merge and t == (LineType.TEXT, LineType.TEXT):
            last_line = merge_lines(last_line, line)
        else:  # Should start up a new paragraph
            yield last_line
            last_line = line
    yield last_line


@utils.curry_first_arg
def to_epub(opt: ConvertOptions, title, toc, lines: LineIter) -> str:
    """Make an ePub file from lines (paragraphs) and meta information."""

    def toc_to_html(toc):
        if len(toc) == 0:
            return ''
        title = '目录' if any(0x4e00 <= ord(ch) <= 0x9fff for ch in ''.join(t[1] for t in toc)) else 'Table of Contents'
        html = '<h2>%s</h2><div style="line-height: 0; margin-bottom: 50vh;">' % (title,)
        for t in toc:
            html += '<p style="margin-left: %dpx;">' % ((t[0] - 1) * 20,) + t[1] + '</p>'
        html += '</div>'
        return html
        # if not isinstance(toc, list):
        #     return toc
        # return ''.join('<p>%s</p>' % (h + '.%d ' % (i + 1,) + toc_to_html(j, h + '.%d' % (n,), n + 1),) for i, j in enumerate(toc))

    def span_to_html(span: Span) -> str:
        """Make a span a HTML tag."""

        beg, end = '<span style="%s">', '</span>'
        content = html.escape(span['text'])
        styles = []
        cate, fl = span['flags']
        if cate == 0:
            styles.append('font-family:serif')
        elif cate == 1:
            styles.append('font-family:sans-serif')
        else:
            assert cate == 2
            styles.append('font-family:monospace')
        if fl & 1 << 0:
            styles.append('vertical-align:super')
        if fl & 1 << 1:
            styles.append('font-style:italic')
        if fl & 1 << 2:
            styles.append('font-weight:bold')
        styles.append('color:' + span['color'])
        return beg % ';'.join(styles) + content + end

    def image_to_html(line: Line) -> str:
        tag = '<img width="{width}" height="{height}" src="data:image/{ext};base64,{data}" />'
        return tag.format(
            width=line['width'],
            height=line['height'],
            ext=line['ext'],
            data=base64.b64encode(line['image']).decode())

    def lines_to_html(lines: LineIter) -> str:
        """Convert lines (paragraphs) to an HTML fragment."""

        pars = []
        for line in lines:
            t = line_type(line)
            if t == LineType.TEXT:
                pars.append(''.join(map(span_to_html, line['spans'])))
            elif t == LineType.IMAGE:
                pars.append(image_to_html(line))
        return ''.join('<p>' + par + '</p>' for par in pars)

    html_data = toc_to_html(toc) + lines_to_html(lines)
    # Filter control characters
    html_data = ''.join(ch for ch in html_data if not (ord(ch) < 32 or ord(ch) == 127))
    epub_data = epubgen.EpubData(
        title=title,
        html=html_data
    )
    return epubgen.create_epub(epub_data)


@utils.curry_first_arg
def to_list(opt: ConvertOptions, lines: LineIter) -> list[str]:
    """Convert to a list of paragraphs."""

    lst = []
    for i, line in enumerate(lines):
        t = line_type(line)
        if t == LineType.TEXT:
            par = ''.join(span['text'] for span in line['spans']) \
                .replace(' ', '')
            lst.append(par)
        elif t == LineType.IMAGE:
            par = '[Image witdh=%d height=%d]' % \
                  (line['width'], line['height'])
            lst.append(par)
    return lst


def convert(opt: ConvertOptions, src: str) -> Any:
    # Pass options to each step function as its first argument
    def apply_to(src, steps):
        data = src
        for step in steps:
            data = step(data)
        return data

    title = extract_title(src)
    toc = extract_toc(src)
    pars = apply_to(src, map(lambda fn: fn(opt), [
        extract_rawlines,
        splice_rawlines,
        reformat_rawlines,
        aggregate_lines
    ]))
    epub = to_epub(opt)(title, toc, pars)
    return epub


# if __name__ == '__main__':
#     import os.path
#     import subprocess
#
#     # pdf = os.path.join('dataset/tex-imp.pdf')
#     pdf = os.path.join('dataset/samples/test.pdf')
#     opt = ConvertOptions(
#         vertical=False
#     )
#     epub = convert(opt, pdf)
#     subprocess.run(['open', epub])
#     # print(epub)
#     exit(0)

if __name__ == '__main__':
    import argparse
    import os
    import shutil

    parser = argparse.ArgumentParser(description='Process a PDF document.')
    parser.add_argument('file', nargs='?', type=str)
    parser.add_argument('--vertical', nargs='?', const=True, default=False)
    parser.add_argument('--name', type=str)
    args = parser.parse_args()
    pdf = args.file
    opt = ConvertOptions(
        vertical=args.vertical
    )
    if pdf is None:
        for root, dirs, files in os.walk('/app/pdf', topdown=False):
            for name in files:
                pn, ext = os.path.splitext(name)
                if ext == '.pdf':
                    full_path = os.path.join(root, name)
                    epub = convert(opt, full_path)
                    epub_path = os.path.join(root, pn + '.epub')
                    shutil.move(epub, epub_path)
                    print(epub_path)
    else:
        real_pdf = os.path.join('/app/pdf', pdf)
        pn, ext = os.path.splitext(real_pdf)
        epub = convert(opt, real_pdf)
        name = args.name if args.name is not None else pn
        epub_path = os.path.join('/app/pdf', name + '.epub')
        shutil.move(epub, epub_path)
        print(epub_path)
