export type Recommendation = {
  title: string
  keywords: string[]
  description: string
  // 圖片檔名，網址由 whiskyImageUrl 組出
  image: string | null
}

export type ChatResponse = {
  recommendations: Recommendation[]
}

// 只代表「可以直接顯示給使用者看」的錯誤，其他例外照常往上拋
export class ChatError extends Error {}

export async function askQuestion(question: string): Promise<ChatResponse> {
  let response: Response
  try {
    response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
  } catch (error) {
    // fetch 只有在網路層失敗時才會丟 TypeError
    if (error instanceof TypeError) {
      throw new ChatError('無法連線到伺服器。請確認後端已啟動，再重新提問。')
    }
    throw error
  }

  if (response.status === 422) {
    throw new ChatError('問題需要介於 1 到 1000 字之間。')
  }
  if (!response.ok) {
    // 後端沒啟動時，Vite proxy 也會回 5xx，所以一併提示檢查後端
    throw new ChatError(
      `伺服器沒有正常回應（狀態碼 ${response.status}）。請確認後端已啟動，再重新提問。`,
    )
  }
  return response.json()
}
