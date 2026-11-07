<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'

// 後端是一次請求、沒有回報進度，這裡依實測的各步驟耗時推進畫面；
// 最後一步（LLM 撰寫）最久且時間不定，停在那裡直到回答出現
const steps = [
  { label: '理解你想要的風味', startsAt: 0 },
  { label: '從品飲筆記中找出候選', startsAt: 3 },
  // 檢索與 re-rank 合計約 1 到 1.5 秒
  { label: '依筆記撰寫香氣、口感與尾韻', startsAt: 4.5 },
]

const elapsed = ref(0)
const startedAt = Date.now()
const timer = window.setInterval(() => {
  elapsed.value = (Date.now() - startedAt) / 1000
}, 250)

onUnmounted(() => window.clearInterval(timer))

const currentIndex = computed(() => {
  let index = 0
  steps.forEach((step, i) => {
    if (elapsed.value >= step.startsAt) {
      index = i
    }
  })
  return index
})
</script>

<template>
  <div class="loading" role="status">
    <ol class="steps">
      <li
        v-for="(step, index) in steps"
        :key="step.label"
        class="step"
        :class="{
          'is-done': index < currentIndex,
          'is-current': index === currentIndex,
        }"
      >
        <span class="marker" aria-hidden="true">{{ index < currentIndex ? '✓' : '' }}</span>
        <span class="label">{{ step.label }}</span>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.steps {
  margin: 0;
  padding: 0;
  list-style: none;
}

.step {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.15rem 0;
  font-size: 0.95rem;
  color: color-mix(in srgb, var(--char) 40%, var(--limewash));
  transition: color 300ms;
}

.step.is-done {
  color: color-mix(in srgb, var(--char) 65%, var(--limewash));
}

.step.is-current {
  color: var(--char);
  font-weight: 700;
}

/* 標記沿用推薦卡標籤的方角與琥珀色：完成的打勾，進行中的像酒液一樣緩慢明暗起伏 */
.marker {
  flex: none;
  display: grid;
  place-items: center;
  width: 1.1rem;
  height: 1.1rem;
  border: 1.5px solid currentColor;
  border-radius: 2px;
  font-size: 0.75rem;
  line-height: 1;
}

.is-done .marker {
  border-color: var(--oak);
  color: var(--oak);
}

.is-current .marker {
  border-color: var(--spirit-deep);
  background: var(--spirit);
  animation: pour 1.4s ease-in-out infinite;
}

@keyframes pour {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.35;
    transform: scale(0.8);
  }
}

/* 進行中的文字後面加上逐一出現的省略號，提示仍在處理 */
.is-current .label::after {
  content: '';
  display: inline-block;
  width: 1.2em;
  text-align: left;
  animation: dots 1.2s steps(4, end) infinite;
}

@keyframes dots {
  0% {
    content: '';
  }
  25% {
    content: '.';
  }
  50% {
    content: '..';
  }
  75% {
    content: '...';
  }
}
</style>
