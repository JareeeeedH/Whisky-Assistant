<script setup lang="ts">
import { ref } from 'vue'
import { whiskyImageUrl } from '../whiskyImage'

// 從資料庫挑出的原廠裝瓶照片（知名酒廠、評分 90 以上、直式且確認檔案存在）；
// 寫死在前端，首頁不必為了裝飾多打一次 API
const pool = [
  'Benromach-40-yo-Heritage.jpg',
  'Lagavulin-12-OB.jpg',
  'Talisker-10-yo.jpg',
  'Lagavulin-26-yo-1991-Casks-of-Distinction.jpg',
  'Benromach-50-yo-1969.jpg',
  'Springbank-1972-OB.jpg',
  'Macallan-25-yo-1965.jpg',
  'Glenfarclas-1994-1580.jpg',
  'Springbank-12-1978.jpg',
  'Highland-Park-30-yo-OB.jpg',
  'Talisker-33-yo-1992-2026-60-1-OB-Rare-Series-331-bottles.jpg',
  'Glenfarclas-2003-ask-2.jpg',
  'Springbank-25-yo-1993-OB-private-for-Feinkost-Reifferscheid.jpg',
  'Springbank-30-yo-1993-Private-Bottling-Michiel-Wigman-157.jpg',
  'Clynelish-5.jpg',
  'Macallan-25-yo-1965-M.jpg',
  'Benromach-2013-Whisky-Club-Nantais.jpg',
  'Springbank-1995-Private-Bottling.jpg',
  'Lagavulin-25-yo-200th-Anniversary.jpg',
  'Brora-1981-Prima-Ultima-Third-Release.jpg',
  'Laphroaig-15-yo-Buckingham-Wile-Co-Lake-Success.jpg',
  'Ardbeg-21-yo-Twenty-One.jpg',
  'Highland-Park-13-yo-2005--Viking-Line.jpg',
  'Glenfarclas-43-yo-1977-private-for-Jeroboams.jpg',
]

const WALL_SIZE = 9

// 每次打開首頁換一批，讓重複造訪的人看到不同的酒
function pickRandom(items: string[], count: number): string[] {
  const shuffled = [...items]
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled.slice(0, count)
}

const bottles = ref(pickRandom(pool, WALL_SIZE))
const failed = ref(new Set<string>())
</script>

<template>
  <!-- 純裝飾，酒名不重要，對螢幕閱讀器隱藏 -->
  <div class="wall" aria-hidden="true">
    <div
      v-for="(bottle, index) in bottles"
      :key="bottle"
      class="label"
      :style="{ '--order': index }"
    >
      <div class="frame">
        <img
          v-if="!failed.has(bottle)"
          :src="whiskyImageUrl(bottle) ?? undefined"
          alt=""
          @error="failed.add(bottle)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.wall {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.1rem;
}

/* 像釘在酒窖牆上的酒標：白邊、各自略微歪斜，奇偶交錯讓牆面不死板 */
.label {
  aspect-ratio: 3 / 4;
  padding: 0.35rem;
  background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--oak) 45%, transparent);
  transform: rotate(-2deg);
  animation: pin 500ms cubic-bezier(0.2, 0.9, 0.3, 1.1) both;
  animation-delay: calc(var(--order) * 70ms);
}

.label:nth-child(even) {
  transform: rotate(1.5deg) translateY(0.6rem);
}

.label:nth-child(3n) {
  transform: rotate(-0.5deg) translateY(-0.4rem);
}

/* 白邊留在 .label 的 padding，照片的裁切只在內框裡進行 */
.frame {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: color-mix(in srgb, var(--oak) 18%, var(--limewash));
}

/* 原圖自帶黃色外框：放大後讓外框落在容器外被裁掉，作法同推薦卡 */
.frame img {
  position: absolute;
  inset: -10%;
  width: 120%;
  height: 120%;
  object-fit: cover;
}

/* 首頁唯一的進場動態：酒標依序貼上牆 */
@keyframes pin {
  from {
    opacity: 0;
    translate: 0 -0.8rem;
  }
  to {
    opacity: 1;
    translate: 0 0;
  }
}
</style>
