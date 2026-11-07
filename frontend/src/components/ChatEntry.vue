<script setup lang="ts">
import type { Entry } from '../types'
import LoadingSteps from './LoadingSteps.vue'
import RecommendationList from './RecommendationList.vue'

defineProps<{ entry: Entry }>()
</script>

<template>
  <article class="entry">
    <h2 class="question">{{ entry.question }}</h2>

    <LoadingSteps v-if="entry.status === 'loading'" />

    <p v-if="entry.error" class="error" role="alert">{{ entry.error }}</p>

    <!-- 提示是在引導怎麼問，不是系統出錯，所以用一般內文而不是錯誤樣式 -->
    <p v-if="entry.notice" class="notice">{{ entry.notice }}</p>

    <RecommendationList
      v-if="entry.recommendations && entry.recommendations.length > 0"
      :recommendations="entry.recommendations"
    />
  </article>
</template>

<style scoped>
.entry {
  padding: 2rem 0;
  border-bottom: 1px solid var(--oak);
}

.question {
  margin: 0 0 1rem;
  max-width: var(--measure);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.45;
}

.notice {
  margin: 0;
  max-width: var(--measure);
}

.error {
  margin: 1rem 0 0;
  max-width: var(--measure);
  padding-left: 0.9rem;
  border-left: 3px solid var(--char);
  font-weight: 700;
}
</style>
