<script setup lang="ts">
import type { Entry } from '../types'
import RecommendationList from './RecommendationList.vue'

defineProps<{ entry: Entry }>()
</script>

<template>
  <article class="entry">
    <h2 class="question">{{ entry.question }}</h2>

    <p v-if="entry.status === 'loading'" class="waiting">正在挑選酒款…</p>
    <p v-else-if="entry.summary" class="summary">{{ entry.summary }}</p>

    <p v-if="entry.error" class="error" role="alert">{{ entry.error }}</p>

    <RecommendationList
      v-if="entry.recommendations && entry.recommendations.length > 0"
      :recommendations="entry.recommendations"
    />
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

.summary {
  margin: 0;
  max-width: var(--measure);
  white-space: pre-line;
}

.error {
  margin: 1rem 0 0;
  max-width: var(--measure);
  padding-left: 0.9rem;
  border-left: 3px solid var(--char);
  font-weight: 700;
}
</style>
