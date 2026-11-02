<script setup lang="ts">
import { computed } from 'vue'
import { renderAnswer } from '../markdown'
import type { Entry } from '../types'
import SourceList from './SourceList.vue'

const props = defineProps<{ entry: Entry }>()

const answerHtml = computed(() => renderAnswer(props.entry.answer, props.entry.id))
const isWaiting = computed(() => props.entry.status === 'loading')

function openSource(event: MouseEvent): void {
  if (!(event.target instanceof Element)) {
    return
  }
  const mark = event.target.closest<HTMLAnchorElement>('a.cask-mark')
  if (mark === null) {
    return
  }
  event.preventDefault()
  const source = document.getElementById(mark.hash.slice(1))
  if (!(source instanceof HTMLDetailsElement)) {
    return
  }
  source.open = true
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  source.scrollIntoView({ block: 'nearest', behavior: reduceMotion ? 'auto' : 'smooth' })
  source.querySelector('summary')?.focus({ preventScroll: true })
}
</script>

<template>
  <article class="entry">
    <h2 class="question">{{ entry.question }}</h2>

    <p v-if="isWaiting" class="waiting">正在查閱資料…</p>
    <div v-else class="answer" @click="openSource" v-html="answerHtml" />

    <p v-if="entry.error" class="error" role="alert">{{ entry.error }}</p>

    <SourceList v-if="entry.sources" :entry-id="entry.id" :sources="entry.sources" />
  </article>
</template>

<style scoped>
.entry {
  padding: 2.5rem 0 2.25rem;
  border-bottom: 1px solid var(--oak);
}

.question {
  margin: 0 0 1rem;
  max-width: var(--measure);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.45;
}

.waiting {
  margin: 0;
}

.answer {
  max-width: var(--measure);
}

.answer :deep(p),
.answer :deep(ul),
.answer :deep(ol) {
  margin: 0 0 0.9em;
}

.answer :deep(ul),
.answer :deep(ol) {
  padding-left: 1.4em;
}

.answer :deep(> :last-child) {
  margin-bottom: 0;
}

/* 桶號標記：回答出現時依出現順序蓋章 */
.answer :deep(.cask-mark) {
  display: inline-block;
  margin: 0 0.15em;
  padding: 0 0.3em;
  border: 1.5px solid currentColor;
  border-radius: 2px;
  font-family: var(--font-stencil);
  font-size: 0.8em;
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.04em;
  color: var(--sherry);
  text-decoration: none;
  vertical-align: 0.1em;
  transform: rotate(-4deg);
  animation: stamp 260ms cubic-bezier(0.2, 0.9, 0.3, 1.2) both;
  animation-delay: calc(var(--order) * 140ms);
}

.answer :deep(.cask-mark:hover) {
  background: var(--sherry);
  color: var(--limewash);
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

.error {
  margin: 1rem 0 0;
  max-width: var(--measure);
  padding-left: 0.9rem;
  border-left: 3px solid var(--char);
  font-weight: 700;
}
</style>
