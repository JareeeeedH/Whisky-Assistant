import type { Source } from './api/chat'

export type Entry = {
  id: number
  question: string
  answer: string
  // null 代表還沒拿到回答；空陣列代表這次回答沒有引用來源
  sources: Source[] | null
  status: 'loading' | 'done' | 'error'
  error: string | null
}
