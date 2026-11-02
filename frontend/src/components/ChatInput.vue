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
        placeholder="輸入你的威士忌問題"
      />
      <button type="submit" :disabled="disabled || text.trim() === ''">提問</button>
    </div>
  </form>
</template>

<style scoped>
.composer.is-docked {
  position: fixed;
  inset: auto 0 0;
  padding: 1rem 0 0.75rem;
  background: var(--limewash);
  border-top: 1px solid var(--oak);
}

/* 固定在底部時脫離了 App.vue 的 .page，要自己補上同寬同內距才會和內容欄對齊 */
.is-docked .inner {
  max-width: 40rem;
  margin-inline: auto;
  padding-inline: var(--gutter);
}

.inner {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
}

textarea {
  flex: 1;
  max-height: 12rem;
  padding: 0.35rem 0;
  border: 0;
  border-bottom: 1px solid var(--oak);
  border-radius: 0;
  background: transparent;
  line-height: 1.6;
  resize: none;
}

textarea::placeholder {
  color: var(--char);
  opacity: 0.6;
}

textarea:focus-visible {
  outline: none;
  border-bottom-color: var(--spirit-deep);
  box-shadow: 0 1px 0 var(--spirit-deep);
}

button {
  flex: none;
  padding: 0.35rem 1.2rem;
  border: 0;
  border-radius: 2px;
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
