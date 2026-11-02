<script setup lang="ts">
import type { Source } from '../api/chat'
import { padCaskNumber } from '../markdown'

defineProps<{ entryId: number; sources: Source[] }>()
</script>

<template>
  <section class="sources">
    <h3 class="heading">來源</h3>
    <p v-if="sources.length === 0" class="empty">這次回答沒有引用知識庫資料。</p>
    <details v-for="source in sources" :id="`source-${entryId}-${source.id}`" :key="source.id">
      <summary>
        <span class="cask-number">{{ padCaskNumber(source.id) }}</span>
        <span class="title">{{ source.title }}</span>
      </summary>
      <div class="excerpt">
        <p>{{ source.content }}</p>
        <p v-if="source.source" class="origin">{{ source.source }}</p>
      </div>
    </details>
  </section>
</template>

<style scoped>
.sources {
  margin-top: 1.75rem;
  max-width: var(--measure);
}

.heading {
  margin: 0 0 0.25rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px dashed var(--oak);
  font-size: 0.9rem;
  font-weight: 700;
}

.empty {
  margin: 0.5rem 0 0;
  font-size: 0.95rem;
}

details {
  border-bottom: 1px dashed var(--oak);
}

summary {
  display: grid;
  grid-template-columns: 2.5rem 1fr auto;
  align-items: baseline;
  padding: 0.45rem 0;
  cursor: pointer;
  list-style: none;
}

summary::-webkit-details-marker {
  display: none;
}

/* 展開狀態用三角形方向表示，箭頭本身就是狀態資訊 */
summary::after {
  content: '▸';
  transition: transform 160ms ease-out;
}

details[open] summary::after {
  transform: rotate(90deg);
}

.cask-number {
  font-family: var(--font-stencil);
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--sherry);
}

.title {
  font-size: 0.95rem;
}

.excerpt {
  padding: 0 0 0.9rem 2.5rem;
  font-size: 0.95rem;
}

.excerpt p {
  margin: 0;
}

.excerpt .origin {
  margin-top: 0.35rem;
  font-size: 0.85rem;
  word-break: break-all;
}
</style>
