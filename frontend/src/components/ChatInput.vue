<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

// docked：固定在畫面底部；否則跟著版面排在原地（空白狀態時放在畫面中央）
const props = defineProps<{ disabled: boolean; docked: boolean }>()
const emit = defineEmits<{ submit: [question: string] }>()

// 草稿由外層持有：點範例問題時要能從外面填入，輸入框從中央換到底部時內容也不會消失
const text = defineModel<string>({ required: true })
const textarea = ref<HTMLTextAreaElement | null>(null)

// 文字可能從外面被改掉（填入範例、送出後清空），所以監看內容來調整高度，而不是只聽 input 事件
watch(text, () => nextTick(resize))

function resize(): void {
  const el = textarea.value
  if (el === null) {
    return
  }
  // 先歸零才能量到內容實際需要的高度，否則只會變高不會變矮
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

function submit(): void {
  const question = text.value.trim()
  if (question === '' || props.disabled) {
    return
  }
  emit('submit', question)
  text.value = ''
}

function focusAtEnd(): void {
  const el = textarea.value
  if (el === null) {
    return
  }
  el.focus()
  el.setSelectionRange(el.value.length, el.value.length)
}

defineExpose({ focusAtEnd })
</script>

<template>
  <form class="composer" :class="{ 'is-docked': docked }" @submit.prevent="submit">
    <div class="inner">
      <label class="visually-hidden" for="question">你的問題</label>
      <textarea
        id="question"
        ref="textarea"
        v-model="text"
        rows="1"
        maxlength="1000"
        placeholder="輸入你想找的威士忌風味"
      />
      <button type="submit" :disabled="disabled || text.trim() === ''">提問</button>
    </div>
  </form>
</template>

<style scoped>
/* App.vue 以 flex 把畫面分成頁首、對話框、輸入框三段，輸入框自然停在底部，不必 fixed */
.composer.is-docked {
  flex: none;
  padding: 0.75rem var(--gutter);
}

/* 輸入框不在 App.vue 的 .page 裡（沒有左右 gutter），寬度要扣掉 gutter 才會和對話框對齊 */
.is-docked .inner {
  max-width: calc(var(--page-width) - 2 * var(--gutter));
  margin-inline: auto;
}

/* 外框包住輸入區和按鈕，整塊像一張可以書寫的帳冊欄位 */
.inner {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  padding: 0.5rem 0.5rem 0.5rem 1rem;
  border: 1.5px solid var(--char);
  border-radius: 4px;
  background: var(--paper);
}

/* 鍵盤焦點落在 textarea，但外框才是使用者看到的輸入框，所以焦點樣式畫在外框上 */
.inner:focus-within {
  border-color: var(--spirit-deep);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--spirit-deep) 25%, transparent);
}

textarea {
  flex: 1;
  max-height: 12rem;
  padding: 0.4rem 0;
  border: 0;
  background: transparent;
  font-size: 1.05rem;
  line-height: 1.6;
  resize: none;
}

/* 空白狀態的輸入框是頁面主角，留白與高度都放大，看起來就是要你寫字的地方 */
.composer:not(.is-docked) .inner {
  padding: 0.75rem 0.75rem 0.75rem 1.25rem;
}

.composer:not(.is-docked) textarea {
  min-height: 6rem;
  font-size: 1.1rem;
}

textarea::placeholder {
  color: var(--char);
  opacity: 0.6;
}

textarea:focus-visible {
  outline: none;
}

button {
  flex: none;
  padding: 0.5rem 1.3rem;
  border: 0;
  border-radius: 3px;
  background: var(--char);
  color: var(--limewash);
  font-weight: 700;
  cursor: pointer;
}

button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
</style>
