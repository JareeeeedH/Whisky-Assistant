<script setup lang="ts">
import { ref } from 'vue'
import type { Recommendation } from '../api/chat'
import { whiskyImageUrl } from '../whiskyImage'

defineProps<{ recommendations: Recommendation[] }>()

// 圖片庫有少數檔案缺漏，載入失敗就整個不顯示，不留破圖
const failedImages = ref(new Set<string>())

function imageUrl(item: Recommendation): string | null {
  if (item.image === null || failedImages.value.has(item.image)) {
    return null
  }
  return whiskyImageUrl(item.image)
}

function markFailed(image: string | null): void {
  if (image !== null) {
    failedImages.value.add(image)
  }
}

// 桶號固定兩位數，模仿酒桶端面的噴漆編號
function caskNumber(index: number): string {
  return String(index + 1).padStart(2, '0')
}
</script>

<template>
  <ol class="records">
    <li v-for="(item, index) in recommendations" :key="item.title" class="record">
      <span class="cask-number" :style="{ '--order': index }" aria-hidden="true">
        {{ caskNumber(index) }}
      </span>
      <div class="body">
        <h3 class="title">{{ item.title }}</h3>
        <p class="description">{{ item.description }}</p>
      </div>
      <!-- 酒名已在左側，照片只是輔助辨識，所以 alt 留空避免螢幕閱讀器重複念酒名 -->
      <img
        v-if="imageUrl(item)"
        class="bottle"
        :src="imageUrl(item) ?? undefined"
        alt=""
        loading="lazy"
        @error="markFailed(item.image)"
      />
    </li>
  </ol>
</template>

<style scoped>
.records {
  margin: 1.75rem 0 0;
  max-width: var(--measure);
  padding: 0;
  list-style: none;
  border-top: 1px dashed var(--oak);
}

.record {
  display: grid;
  grid-template-columns: 3.25rem 1fr 4.5rem;
  column-gap: 1rem;
  align-items: start;
  padding: 1.1rem 0 1.2rem;
  border-bottom: 1px dashed var(--oak);
}

/* 條目底部已有實線分隔，最後一筆不再重複一條虛線 */
.record:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

/* 桶號是整個介面唯一的大膽元素：回答出現時依序蓋章 */
.cask-number {
  justify-self: start;
  margin-top: 0.1rem;
  padding: 0 0.3em;
  border: 2px solid currentColor;
  border-radius: 2px;
  font-family: var(--font-stencil);
  font-size: 1.35rem;
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: 0.04em;
  color: var(--sherry);
  transform: rotate(-4deg);
  animation: stamp 260ms cubic-bezier(0.2, 0.9, 0.3, 1.2) both;
  animation-delay: calc(var(--order) * 160ms);
}

@keyframes stamp {
  from {
    opacity: 0;
    transform: scale(1.8) rotate(-12deg);
  }
  to {
    opacity: 1;
    transform: scale(1) rotate(-4deg);
  }
}

.title {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.5;
}

.description {
  margin: 0;
  white-space: pre-line;
}

/* 原圖是約 150px 寬的縮圖，顯示得比原尺寸小才不會模糊 */
.bottle {
  width: 100%;
  height: auto;
  margin-top: 0.3rem;
}

@media (max-width: 30rem) {
  .record {
    grid-template-columns: 2.75rem 1fr 3.5rem;
    column-gap: 0.75rem;
  }
}
</style>
