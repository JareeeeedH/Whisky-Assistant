<script setup lang="ts">
const emit = defineEmits<{ pick: [question: string] }>()

const examples = [
  '泥煤味不重、帶果香的艾雷島威士忌有哪些？',
  '推薦幾支雪莉桶風格、果乾味濃的威士忌',
  '適合新手、口感溫和的日本威士忌',
]
</script>

<template>
  <section class="empty">
    <h1 class="title">想找哪款威士忌呢？</h1>
    <slot />
    <ul class="examples">
      <li v-for="example in examples" :key="example">
        <button type="button" @click="emit('pick', example)">{{ example }}</button>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.empty {
  padding: 2rem 0;
}

.title {
  margin: 0 0 2rem;
  font-size: clamp(2rem, 6vw, 2.75rem);
  font-weight: 700;
  line-height: 1.3;
}

.examples {
  margin: 2.5rem 0 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--oak);
}

.examples li {
  border-bottom: 1px solid var(--oak);
}

button {
  display: block;
  width: 100%;
  padding: 0.55rem 0;
  border: 0;
  background: none;
  font-size: 0.9rem;
  text-align: left;
  text-wrap: pretty;
  cursor: pointer;
}

button:hover {
  text-decoration: underline;
  text-decoration-color: var(--oak);
  text-underline-offset: 0.3em;
}
</style>
