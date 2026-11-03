export type WhiskyTitle = {
  name: string
  details: string[]
}

// 酒名格式是「酒名 (濃度, 裝瓶商, 桶型, …)」：括號前當標題，括號內拆成細節
export function splitWhiskyTitle(title: string): WhiskyTitle {
  const open = title.indexOf('(')
  if (open === -1) {
    return { name: title.trim(), details: [] }
  }
  const name = title.slice(0, open).trim()
  const inside = title.slice(open + 1).replace(/\)\s*$/, '')
  const details = []
  for (const part of inside.split(',')) {
    const detail = part.trim()
    if (detail !== '') {
      details.push(detail)
    }
  }
  return { name, details }
}

// 括號內前兩項固定是濃度與裝瓶商；桶號、瓶數等收藏家資訊對一般讀者沒有幫助，不顯示
export function briefDetails(details: string[]): string {
  const brief = []
  for (const detail of details.slice(0, 2)) {
    // OB 是 official bottling 的縮寫，一般讀者看不懂
    brief.push(detail === 'OB' ? '原廠裝瓶' : detail)
  }
  return brief.join(' / ')
}
