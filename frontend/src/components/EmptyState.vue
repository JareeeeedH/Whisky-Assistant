<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ pick: [question: string] }>()

// 口語寫法貼近使用者實際會打的句子；每題示範一種問法（桶型、多重風味、專業條件、指定酒款）。
// 避開單純否定與價格：前者檢索仍會出錯，後者資料沒有
const examples = [
  '想找雪莉桶、果乾味濃、香甜一點的',
  '有沒有喝起來像巧克力、橘子皮的？',
  '想找雪莉桶熟成、帶一點泥煤煙燻，有黑巧克力和皮革調性的',
  // 指定酒款選一甜一煙的經典款，資料庫裡都有多個年份版本可以比較
  'Macallan 18 喝起來如何？',
  'Lagavulin 16 是什麼風味？',
]

// 不放果香、花香、橡木這類幾乎每篇筆記都有的詞，選了等於沒選；後三個是較有辨識度的風味
const flavors = ['蜂蜜', '果乾', '堅果', '巧克力', '辛香料', '海風', '泥煤', '熱帶水果', '皮革', '蠟質']

// 依點選順序保存，組出的句子才會和使用者點的順序一致
const selectedFlavors = ref<string[]>([])

function caskNumber(index: number): string {
  return String(index + 1).padStart(2, '0')
}

function pickExample(example: string): void {
  // 改用範例問題時，輸入框已不是 tag 組出的句子，清掉選取避免畫面和內容不一致
  selectedFlavors.value = []
  emit('pick', example)
}

function toggleFlavor(flavor: string): void {
  if (selectedFlavors.value.includes(flavor)) {
    selectedFlavors.value = selectedFlavors.value.filter((item) => item !== flavor)
  } else {
    selectedFlavors.value = [...selectedFlavors.value, flavor]
  }
  if (selectedFlavors.value.length === 0) {
    emit('pick', '')
    return
  }
  emit('pick', `想找有${selectedFlavors.value.join('、')}風味的`)
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
        <button type="button" @click="pickExample(example)">
          <!-- 和結果頁同樣的桶號，讓首頁也帶到酒窖帳冊的識別；這裡不蓋章，動態只留給回答出現時 -->
          <span class="cask-number" aria-hidden="true">{{ caskNumber(index) }}</span>
          <span class="text">{{ example }}</span>
        </button>
      </li>
    </ul>
    <p class="examples-heading">或用風味挑選</p>
    <div class="flavors">
      <button
        v-for="flavor in flavors"
        :key="flavor"
        type="button"
        class="flavor"
        :aria-pressed="selectedFlavors.includes(flavor)"
        @click="toggleFlavor(flavor)"
      >
        {{ flavor }}
      </button>
    </div>
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

.examples button {
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

.flavors {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

/* 外觀沿用推薦卡「香氣／口感／尾韻」標籤的小方角，讓風味詞和結果頁的風味標籤看起來是同一套 */
.flavor {
  padding: 0.2rem 0.55rem;
  border: 1px solid var(--char);
  border-radius: 2px;
  background: none;
  font-size: 0.85rem;
  line-height: 1.6;
  cursor: pointer;
}

/* 選取狀態用和結果頁標籤相同的琥珀淡色，提示這些詞會出現在輸入框裡 */
.flavor[aria-pressed='true'] {
  background: color-mix(in srgb, var(--spirit) 30%, var(--limewash));
  font-weight: 700;
}

.examples button:hover .text {
  text-decoration: underline;
  text-decoration-color: var(--oak);
  text-underline-offset: 0.3em;
}
</style>
