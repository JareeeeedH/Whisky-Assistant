import logging

from fastapi import FastAPI

from app.chat import answer_question
from app.schemas import ChatRequest, ChatResponse

# uvicorn 只設定自己的 logger；只開啟本專案的 INFO，避免套件的 INFO 紀錄洗版
logging.basicConfig(format="%(levelname)s:     %(name)s - %(message)s")
logging.getLogger("app").setLevel(logging.INFO)

app = FastAPI(title="Whiskey Assistant")


@app.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    return answer_question(request.question)
