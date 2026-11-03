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
