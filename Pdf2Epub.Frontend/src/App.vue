<script setup lang="ts">
import Uploader from "./components/Uploader.vue";
import { NGrid
       , NGridItem
       , NTabs
       , NTabPane
       , NCard
       } from "naive-ui/es";
</script>

<template>
    <div class="app">
        <n-tabs type="line" animated>
            <template #prefix>a logo goes here</template>
            <n-tab-pane name="converter" tab="转换器">
                <n-card>
                    <h2>文件转换器</h2>
                    <h3>批量转换PDF文档为ePub电子书</h3>
                    <uploader />
                </n-card>
            </n-tab-pane>
            <n-tab-pane name="features" tab="特性">
                <n-grid :x-gap="12" :y-gap="8" :cols="3">
                    <n-grid-item>
                        <n-card title="各类版式">
                            横排、竖排、双栏……
                        </n-card>
                    </n-grid-item>
                    <n-grid-item>
                        <n-card title="语言适配">
                            用合适的方式分别处理中文、西文文章
                        </n-card>
                    </n-grid-item>
                    <n-grid-item>
                        <n-card title="保留样式">
                            保留原文档文字的原有样式
                        </n-card>
                    </n-grid-item>
                    <n-grid-item>
                        <n-card title="正确分段">
                            根据文章内容将文字行汇聚为自然段
                        </n-card>
                    </n-grid-item>
                    <n-grid-item>
                        <n-card title="无损转换">
                            保留原文章标题、作者、目录等信息，使其不丢失
                        </n-card>
                    </n-grid-item>
                    <n-grid-item>
                        <n-card title="高效转换">
                            速度快（存疑）
                        </n-card>
                    </n-grid-item>
                </n-grid>
            </n-tab-pane>
            <n-tab-pane name="about" tab="关于">
                <p>团队信息：團団团（2106280）</p>
                <p>团队成员：戴宇轩、梁天宇、高珏霖</p>
            </n-tab-pane>
        </n-tabs>
    </div>
</template>

<style scoped>
.app {
    padding-left: 10px;
    padding-right: 10px;
}
.light-green {
  height: 108px;
  background-color: rgba(0, 128, 0, 0.12);
}
.green {
  height: 108px;
  background-color: rgba(0, 128, 0, 0.24);
}
</style>
