<script setup lang="ts">
import { ref } from 'vue'
import type { Recommendation } from '../api/chat'
import { whiskyImageUrl } from '../whiskyImage'
import { briefDetails, splitWhiskyTitle } from '../whiskyTitle'

defineProps<{ recommendations: Recommendation[] }>()

// 圖片庫有少數檔案缺漏，載入失敗就改顯示空白底，不留破圖
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
      <div class="photo">
        <!-- 酒名就在右側，照片只是輔助辨識，alt 留空避免螢幕閱讀器重複念酒名 -->
        <img
          v-if="imageUrl(item)"
          :src="imageUrl(item) ?? undefined"
          alt=""
          loading="lazy"
          @error="markFailed(item.image)"
        />
        <span class="cask-number" :style="{ '--order': index }" aria-hidden="true">
          {{ caskNumber(index) }}
        </span>
      </div>

      <div class="head">
        <h3 class="name">{{ splitWhiskyTitle(item.title).name }}</h3>
        <p v-if="splitWhiskyTitle(item.title).details.length > 0" class="details">
          {{ briefDetails(splitWhiskyTitle(item.title).details) }}
        </p>
      </div>

      <div class="body">
        <p class="tagline">{{ item.tagline }}</p>
        <dl class="notes">
          <div>
            <dt>香氣</dt>
            <dd>{{ item.nose }}</dd>
          </div>
          <div>
            <dt>口感</dt>
            <dd>{{ item.palate }}</dd>
          </div>
          <div>
            <dt>尾韻</dt>
            <dd>{{ item.finish }}</dd>
          </div>
        </dl>
      </div>
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

/* 照片在左、酒名在右上；寬螢幕時內文改跨滿整欄（見下方 media query） */
.record {
  display: grid;
  grid-template-columns: 6.5rem 1fr;
  grid-template-areas:
    'photo head'
    'photo body';
  grid-template-rows: auto 1fr;
  column-gap: 1.25rem;
  align-items: start;
  padding: 1.5rem 0;
  border-bottom: 1px dashed var(--oak);
}

.photo {
  grid-area: photo;
}

.head {
  grid-area: head;
}

.body {
  grid-area: body;
}

/* 條目底部已有實線分隔，最後一筆不再重複一條虛線 */
.record:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

/* 原圖自帶黃色外框：放大後讓外框落在容器外被裁掉 */
.photo {
  position: relative;
  aspect-ratio: 3 / 4;
  overflow: hidden;
  background: color-mix(in srgb, var(--oak) 18%, var(--limewash));
}

/* inset 的上下百分比依高度、左右依寬度計算，四邊才會裁掉相同比例 */
.photo img {
  position: absolute;
  inset: -10%;
  width: 120%;
  height: 120%;
  object-fit: cover;
}

/* 桶號是整個介面唯一的大膽元素：蓋在照片角落，回答出現時依序蓋章 */
.cask-number {
  position: absolute;
  top: 0.4rem;
  left: 0.4rem;
  padding: 0 0.3em;
  border: 2px solid currentColor;
  border-radius: 2px;
  background: var(--limewash);
  font-family: var(--font-stencil);
  font-size: 1.2rem;
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

.name {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  line-height: 1.35;
}

.details {
  margin: 0.15rem 0 0;
  font-size: 0.85rem;
  line-height: 1.5;
}

/* 一句話印象是每筆的重點，用比內文大的字級讓眼睛先停在這裡 */
.tagline {
  margin: 0.8rem 0 0;
  font-size: 1.1rem;
  line-height: 1.6;
}

.notes {
  display: grid;
  gap: 0.45rem;
  margin: 0.9rem 0 0;
}

.notes div {
  display: grid;
  grid-template-columns: auto 1fr;
  column-gap: 0.75rem;
  align-items: baseline;
}

/* 琥珀色只用在這三個標籤上，讓冷色的頁面帶一點酒色，又不搶桶號的風頭 */
.notes dt {
  padding: 0 0.45em;
  border-radius: 2px;
  background: color-mix(in srgb, var(--spirit) 30%, var(--limewash));
  font-size: 0.8rem;
  font-weight: 700;
  line-height: 1.7;
}

.notes dd {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.7;
}

/* 寬螢幕三款並排，方便一眼比較；欄與欄之間用虛線分隔，延續帳冊的分隔方式 */
@media (min-width: 64rem) {
  .records {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    max-width: none;
  }

  /* 照片放大到接近原圖寬度（約 130px，再大會糊），酒名排在照片旁，
     內文改跨滿整欄，三欄才不會因為照片佔寬而把文字擠成細長條 */
  .record {
    grid-template-columns: 8rem 1fr;
    grid-template-areas:
      'photo head'
      'body body';
    grid-template-rows: auto auto;
    /* 三欄會被拉成和最長那欄等高，多出的高度不要分給各列，內文才會從同一個高度開始 */
    align-content: start;
    column-gap: 1rem;
    padding: 1.5rem 1.25rem 0;
    border-bottom: none;
  }

  /* 靠上對齊照片上緣：三欄的酒名行數不同，靠下對齊時各欄起點高低不一，上方也會留白 */
  .head {
    align-self: start;
  }

  .record:first-child {
    padding-left: 0;
  }

  .record:last-child {
    padding-right: 0;
  }

  .record + .record {
    border-left: 1px dashed var(--oak);
  }
}

@media (max-width: 30rem) {
  .record {
    grid-template-columns: 4.5rem 1fr;
    column-gap: 0.9rem;
  }

  .cask-number {
    font-size: 1rem;
  }
}
</style>
