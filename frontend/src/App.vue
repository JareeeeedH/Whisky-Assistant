<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { askQuestion, ChatError } from './api/chat'
import ChatEntry from './components/ChatEntry.vue'
import ChatInput from './components/ChatInput.vue'
import EmptyState from './components/EmptyState.vue'
import type { Entry } from './types'

const entries = ref<Entry[]>([])
const isAsking = ref(false)
const draft = ref('')
const centeredInput = ref<InstanceType<typeof ChatInput> | null>(null)
// 開始對話後，捲動發生在對話框內而不是整個頁面，捲動位置要從這個元素讀寫
const scroller = ref<HTMLElement | null>(null)
let nextId = 1

// 範例問題只填入輸入框，讓使用者可以先修改再提問
function pickExample(question: string): void {
  draft.value = question
  centeredInput.value?.focusAtEnd()
}

function isNearBottom(): boolean {
  const el = scroller.value
  if (el === null) {
    return true
  }
  return el.clientHeight + el.scrollTop >= el.scrollHeight - 120
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  const el = scroller.value
  if (el !== null) {
    el.scrollTo({ top: el.scrollHeight })
  }
}

async function ask(question: string): Promise<void> {

  entries.value.push({
    id: nextId,
    question,
    recommendations: null,
    notice: null,
    status: 'loading',
    error: null,
  })
  nextId += 1

  // 要透過 ref 取回 reactive 版本，直接改原本的物件畫面不會更新
  const entry = entries.value[entries.value.length - 1]
  isAsking.value = true
  await scrollToBottom()

  try {
    const result = await askQuestion(question)
    // 等待期間使用者若往上捲去看舊回答，就不要硬把畫面拉回底部
    const follow = isNearBottom()
    entry.recommendations = result.recommendations
    entry.notice = result.notice
    entry.status = 'done'
    if (follow) {
      await scrollToBottom()
    }
  } catch (error) {
    if (!(error instanceof ChatError)) {
      throw error
    }
    entry.status = 'error'
    entry.error = error.message
  } finally {
    isAsking.value = false
  }
}
</script>

<template>
  <!-- 有回答後才放寬頁面：首頁維持窄欄，標題與範例的行寬才舒適 -->
  <div class="app" :class="{ 'has-entries': entries.length > 0 }">
    <header class="page header">
      <span class="logo">Whiskey Assistant</span>
    </header>

    <main ref="scroller" class="page main" :class="{ 'is-empty': entries.length === 0 }">
      <EmptyState v-if="entries.length === 0" @pick="pickExample">
        <ChatInput
          ref="centeredInput"
          v-model="draft"
          :disabled="isAsking"
          :docked="false"
          @submit="ask"
        />
      </EmptyState>
      <ChatEntry v-for="entry in entries" :key="entry.id" :entry="entry" />
    </main>

    <!-- 開始對話後輸入框改放在對話框下方，新的回答只在框內累積，不會把它一路往下推 -->
    <ChatInput
      v-if="entries.length > 0"
      v-model="draft"
      :disabled="isAsking"
      :docked="true"
      @submit="ask"
    />
  </div>
</template>

<style scoped>
/* 頁面寬度做成變數，底部固定的輸入框也讀同一個值來對齊內容欄 */
.app {
  --page-width: 40rem;
}

/* 寬螢幕上三款推薦並排，頁面要放寬才放得下 */
@media (min-width: 64rem) {
  .app.has-entries {
    --page-width: 78rem;
  }
}

/* 明確給寬度：有對話後 .app 改成 flex 欄，子元素搭配 margin auto 會縮成內容寬度 */
.page {
  width: 100%;
  max-width: var(--page-width);
  margin: 0 auto;
  padding: 0 var(--gutter);
}

.header {
  padding-top: 1.25rem;
}

.logo {
  font-family: var(--font-stencil);
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}

/* 有對話後整個畫面固定為一個視窗高，頁首與輸入框不動，只有中間的對話框捲動 */
.app.has-entries {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  /* 輸入框貼齊視窗底緣時視線要移到最下方，留一段底部空白讓它靠近畫面中段 */
  padding-bottom: clamp(1rem, 10vh, 6rem);
}

.has-entries .header {
  flex: none;
}

/* min-height: 0 讓 flex 子元素可以比內容矮，overflow 才會在框內出現卷軸 */
.has-entries .main {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  width: calc(100% - 2 * var(--gutter));
  max-width: calc(var(--page-width) - 2 * var(--gutter));
  margin-top: 1rem;
  padding: 0 1.5rem;
  border: 1px solid var(--oak);
  border-radius: 4px;
  background: color-mix(in srgb, var(--paper) 50%, var(--limewash));
}

/* 框的上緣已經和頁首隔開，第一則不需要再用大留白分段 */
.has-entries .main > :deep(.entry:first-child) {
  padding-top: 1rem;
}

/* 框線已經包住對話，最後一則不再畫底線，避免和框的下緣疊成兩條 */
.has-entries .main > :deep(.entry:last-child) {
  border-bottom: none;
}

/* 不再垂直置中：置中時標題離頁首太遠，高螢幕上會留一大片空白；改成固定的上方留白，靠近頁首 */
.main.is-empty {
  padding-top: 3vh;
  padding-bottom: 4rem;
}
</style>
