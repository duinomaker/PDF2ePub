using SqlSugar;

namespace Pdf2Epub.API.Models
{
    public class ConvertTaskModel
    {
        [SugarColumn(IsPrimaryKey = true)]
        public Guid id { get; set; }

        public ConvertStatus? status { get; set; }

        public string? file_name { get; set; }

        public DateTime start_time { get; set; }

        public Guid? worker_id { get; set; }

        public DateTime? end_time { get; set; }

    }
}
