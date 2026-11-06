import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.chat import answer_question
from app.schemas import ChatRequest, ChatResponse

# uvicorn 只設定自己的 logger；只開啟本專案的 INFO，避免套件的 INFO 紀錄洗版
logging.basicConfig(format="%(levelname)s:     %(name)s - %(message)s")
logging.getLogger("app").setLevel(logging.INFO)

app = FastAPI(title="Whiskey Assistant")

# 部署時前端在另一個網域，瀏覽器要後端明確允許才會送出請求；
# 本機開發走 Vite proxy 是同源，不設定 CORS_ORIGINS 就不加這層
cors_origins = os.environ.get("CORS_ORIGINS", "")
if cors_origins != "":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins.split(","),
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )


@app.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    return answer_question(request.question)
