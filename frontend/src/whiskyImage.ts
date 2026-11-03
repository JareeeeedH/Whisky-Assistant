const IMAGE_ROOT = 'https://raw.githubusercontent.com/JareeeeedH/fundata/master/whiskyfun/'

// 圖片庫依檔名中第一個英文字母分成 A–Z 資料夾，路徑區分大小寫；
// 檔名以 _ 或數字開頭時也一樣取第一個英文字母，例如 3-ships.jpg 在 S/
export function whiskyImageUrl(fileName: string): string | null {
  const letter = fileName.match(/[A-Za-z]/)?.[0]
  if (letter === undefined) {
    return null
  }
  return `${IMAGE_ROOT}${letter.toUpperCase()}/${encodeURIComponent(fileName)}`
}
