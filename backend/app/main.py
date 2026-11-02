from fastapi import FastAPI

from app.chat import answer_question
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Whiskey Assistant")


@app.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    return answer_question(request.question)
