import os

from app.retrieval import retrieve
from app.schemas import ChatResponse, Recommendation, Source

RETRIEVAL_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", "3"))

INSTRUCTIONS = """你是威士忌顧問，請根據下方「資料」回答使用者的問題。

規則：
- 只能使用資料中的內容回答，不要加入資料以外的知識。
- 如果資料無法回答這個問題，直接說明資料中沒有相關資訊，不要猜測或編造。
- 引用資料時，在句末用資料編號標註來源，例如 [1]；同一句引用多筆時寫成 [1][2]。
- 資料是品飲者的個人筆記，轉述風味與評價時要說明這是筆記的描述，不要當成客觀事實。
- 使用繁體中文回答；酒名保留原文。
- 可以使用 Markdown（條列、粗體）讓回答易讀。"""


def build_prompt(question: str, sources: list[Source]) -> str:
    # 編號用 source.id 而非迴圈索引：前端靠 id 把回答中的 [n] 對回來源
    blocks = []
    for source in sources:
        blocks.append(f"[{source.id}]\ntitle: {source.title}\ntext: {source.content}")
    context = "\n\n".join(blocks)
    # 問題放在最後：資料很長，讀完資料緊接著看到問題，模型較不會偏離要回答的內容
    return f"{INSTRUCTIONS}\n\n資料：\n\n{context}\n\n問題：{question}"


def generate(prompt: str) -> str:
    # 暫時直接回傳 prompt：接上 LLM 之前，可以在前端畫面上檢查 build_prompt 組出來的內容
    return prompt


def answer_question(question: str) -> ChatResponse:
    sources = retrieve(question, RETRIEVAL_TOP_K)
    prompt = build_prompt(question, sources)
    answer = generate(prompt)
    # 暫時的對應：LLM 接上之前，總結先放 generate 的輸出（目前就是 prompt），
    # 介紹先放英文原文，讓前端可以先依新格式顯示
    recommendations = []
    for source in sources:
        recommendations.append(Recommendation(title=source.title, description=source.content))
    return ChatResponse(summary=answer, recommendations=recommendations)
