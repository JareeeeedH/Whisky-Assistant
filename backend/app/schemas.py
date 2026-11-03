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


class Recommendation(BaseModel):
    title: str
    description: str


class ChatResponse(BaseModel):
    summary: str
    recommendations: list[Recommendation]
