from typing import Annotated

from pydantic import BaseModel, StringConstraints

# 先去掉前後空白再檢查長度，避免只有空白的問題通過驗證
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ChatRequest(BaseModel):
    question: Question


class Source(BaseModel):
    id: int
    title: str
    source: str | None
    content: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
