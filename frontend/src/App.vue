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
let nextId = 1

// 範例問題只填入輸入框，讓使用者可以先修改再提問
function pickExample(question: string): void {
  draft.value = question
  centeredInput.value?.focusAtEnd()
}

function isNearBottom(): boolean {
  return window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 120
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  window.scrollTo({ top: document.documentElement.scrollHeight })
}

async function ask(question: string): Promise<void> {

  entries.value.push({
    id: nextId,
    question,
    answer: '',
    sources: null,
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
    entry.answer = result.answer
    entry.sources = result.sources
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
  <header class="page header">
    <span class="logo">Whiskey Assistant</span>
  </header>

  <main class="page main" :class="{ 'is-empty': entries.length === 0 }">
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

  <!-- 開始對話後輸入框改固定在底部，新的回答才不會把它一路往下推 -->
  <ChatInput
    v-if="entries.length > 0"
    v-model="draft"
    :disabled="isAsking"
    :docked="true"
    @submit="ask"
  />
</template>

<style scoped>
.page {
  max-width: 40rem;
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

.main {
  padding-bottom: var(--dock-height);
}

/* 扣掉頁首高度後垂直置中；底部多留一些空間，讓內容落在比幾何中心略高的視覺中心 */
.main.is-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: calc(100dvh - 4.5rem);
  padding-bottom: 10vh;
}
</style>
