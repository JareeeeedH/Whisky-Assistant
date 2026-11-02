import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ linkify: true, breaks: true })

export function padCaskNumber(n: number): string {
  return String(n).padStart(2, '0')
}

export function renderAnswer(markdown: string, entryId: number): string {
  // LLM 的輸出不可信任，轉成 HTML 後一定要先消毒
  const html = DOMPurify.sanitize(md.render(markdown))

  // 在消毒之後才插入桶號標記：插入的只有固定結構和數字，不會帶進不可信的 HTML
  let order = 0
  return html.replace(/\[(\d{1,2})\]/g, (_match, digits: string) => {
    const n = Number(digits)
    const mark =
      `<a class="cask-mark" href="#source-${entryId}-${n}" style="--order:${order}" ` +
      `aria-label="來源 ${n}">${padCaskNumber(n)}</a>`
    order += 1
    return mark
  })
}
