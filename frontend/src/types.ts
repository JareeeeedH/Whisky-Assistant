import type { Recommendation } from './api/chat'

export type Entry = {
  id: number
  question: string
  // null 代表還沒拿到回答
  recommendations: Recommendation[] | null
  status: 'loading' | 'done' | 'error'
  error: string | null
}
