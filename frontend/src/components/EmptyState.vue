<script setup lang="ts">
const emit = defineEmits<{ pick: [question: string] }>()

const examples = [
  '泥煤味不重、帶果香的艾雷島威士忌有哪些？',
  '推薦幾支雪莉桶風格、果乾味濃的威士忌',
  '適合新手、口感溫和的日本威士忌',
]

function caskNumber(index: number): string {
  return String(index + 1).padStart(2, '0')
}
</script>

<template>
  <section class="empty">
    <h1 class="title">想找哪款威士忌呢？</h1>
    <p class="subtitle">描述你想要的風味，從一萬四千多篇品飲筆記裡，為你挑出三支。</p>
    <slot />
    <p class="examples-heading">或從這裡開始</p>
    <ul class="examples">
      <li v-for="(example, index) in examples" :key="example">
        <button type="button" @click="emit('pick', example)">
          <!-- 和結果頁同樣的桶號，讓首頁也帶到酒窖帳冊的識別；這裡不蓋章，動態只留給回答出現時 -->
          <span class="cask-number" aria-hidden="true">{{ caskNumber(index) }}</span>
          <span class="text">{{ example }}</span>
        </button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.empty {
  padding: 2rem 0;
}

.title {
  margin: 0;
  font-size: clamp(2rem, 6vw, 2.75rem);
  font-weight: 700;
  line-height: 1.3;
}

.subtitle {
  margin: 0.6rem 0 1.75rem;
  max-width: var(--measure);
  font-size: 1.05rem;
}

.examples-heading {
  margin: 2.25rem 0 0.5rem;
  font-size: 0.85rem;
}

.examples {
  margin: 0;
  padding: 0;
  list-style: none;
  border-top: 1px dashed var(--oak);
}

.examples li {
  border-bottom: 1px dashed var(--oak);
}

button {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  width: 100%;
  padding: 0.6rem 0;
  border: 0;
  background: none;
  text-align: left;
  cursor: pointer;
}

/* 模板字體的數字寬度不一，固定寬度讓三行問題文字對齊 */
.cask-number {
  flex: none;
  width: 2.2em;
  text-align: center;
  border: 1.5px solid currentColor;
  border-radius: 2px;
  font-family: var(--font-stencil);
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.04em;
  color: var(--sherry);
  transform: rotate(-4deg);
}

.text {
  font-size: 0.95rem;
  text-wrap: pretty;
}

button:hover .text {
  text-decoration: underline;
  text-decoration-color: var(--oak);
  text-underline-offset: 0.3em;
}
</style>
