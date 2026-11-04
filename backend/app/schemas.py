from typing import Annotated

from pydantic import BaseModel, StringConstraints

# 先去掉前後空白再檢查長度，避免只有空白的問題通過驗證
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ChatRequest(BaseModel):
    question: Question


# 檢索結果，只在後端內部使用；id 為排名，用來把 LLM 的介紹對回酒款
class Source(BaseModel):
    id: int
    title: str
    source: str | None
    content: str
    image: str | None


class Recommendation(BaseModel):
    title: str
    tagline: str
    nose: str
    palate: str
    finish: str
    # 只給圖片檔名，網址由前端組：圖片放在哪裡是前端顯示的事
    image: str | None


class ChatResponse(BaseModel):
    recommendations: list[Recommendation]
    # 問題不是要找酒時的提示；用獨立欄位，前端才不必從「推薦是空的」猜原因
    notice: str | None = None
