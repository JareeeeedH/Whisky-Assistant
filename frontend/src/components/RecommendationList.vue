<script setup lang="ts">
import type { Recommendation } from '../api/chat'

defineProps<{ recommendations: Recommendation[] }>()

// 桶號固定兩位數，模仿酒桶端面的噴漆編號
function caskNumber(index: number): string {
  return String(index + 1).padStart(2, '0')
}
</script>

<template>
  <ol class="records">
    <li v-for="(item, index) in recommendations" :key="item.title" class="record">
      <span class="cask-number" :style="{ '--order': index }" aria-hidden="true">
        {{ caskNumber(index) }}
      </span>
      <div class="body">
        <h3 class="title">{{ item.title }}</h3>
        <p class="description">{{ item.description }}</p>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.records {
  margin: 1.75rem 0 0;
  max-width: var(--measure);
  padding: 0;
  list-style: none;
  border-top: 1px dashed var(--oak);
}

.record {
  display: grid;
  grid-template-columns: 3.25rem 1fr;
  align-items: start;
  padding: 1.1rem 0 1.2rem;
  border-bottom: 1px dashed var(--oak);
}

/* 桶號是整個介面唯一的大膽元素：回答出現時依序蓋章 */
.cask-number {
  justify-self: start;
  margin-top: 0.1rem;
  padding: 0 0.3em;
  border: 2px solid currentColor;
  border-radius: 2px;
  font-family: var(--font-stencil);
  font-size: 1.35rem;
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: 0.04em;
  color: var(--sherry);
  transform: rotate(-4deg);
  animation: stamp 260ms cubic-bezier(0.2, 0.9, 0.3, 1.2) both;
  animation-delay: calc(var(--order) * 160ms);
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

.title {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.5;
}

.description {
  margin: 0;
  white-space: pre-line;
}
</style>
