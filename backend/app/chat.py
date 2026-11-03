import os

from openai import OpenAI
from pydantic import BaseModel

from app.retrieval import retrieve
from app.schemas import ChatResponse, Recommendation, Source

RETRIEVAL_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", "3"))
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-6-luna")

# 自動讀取環境變數 OPENAI_API_KEY；SDK 預設逾時 10 分鐘，前端會一直顯示載入中，所以縮短
client = OpenAI(timeout=60)

INSTRUCTIONS = """你是威士忌顧問。下方「資料」是幾支威士忌的品飲筆記（英文），
請為每支酒寫一段中文介紹。

要寫的內容：
- 每筆資料各寫一段介紹，約 100 到 200 字，描述這支酒的香氣、口感與尾韻。
- 每筆另外列出 3 個最能代表這支酒的風味關鍵字，每個 2 到 4 個中文字，例如「碘酒」「雪莉果乾」。
- 資料編號填在 id 欄位，介紹內文不要寫出編號。

規則：
- 風味與評價只能來自該筆筆記，不要加入筆記以外的知識；
  可以用生動的中文改寫，但不要誇大或補上筆記沒寫的風味。
- 資料是品飲者的個人筆記，提到評價時要說明是筆記的看法，不要寫成客觀事實。
- 介紹中提到酒名時保留原文，不要翻譯。
- 使用繁體中文，以純文字書寫，不要使用 Markdown 符號。"""


def build_prompt(sources: list[Source]) -> str:
    # 編號用 source.id 而非迴圈索引：後端靠 id 把 LLM 的介紹對回酒款與資料庫的酒名
    blocks = []
    for source in sources:
        blocks.append(f"[{source.id}]\ntitle: {source.title}\ntext: {source.content}")
    context = "\n\n".join(blocks)
    return f"{INSTRUCTIONS}\n\n資料：\n\n{context}"


# LLM 的輸出格式（Structured Outputs）：只回傳編號與介紹，酒名由後端用編號對回資料庫
class Description(BaseModel):
    id: int
    keywords: list[str]
    description: str


class Descriptions(BaseModel):
    items: list[Description]


def generate(prompt: str) -> list[Description]:
    response = client.responses.parse(
        model=LLM_MODEL,
        input=prompt,
        text_format=Descriptions,
    )
    # 模型拒答時沒有可解析的內容
    if response.output_parsed is None:
        raise ValueError("LLM 沒有回傳符合格式的內容")
    return response.output_parsed.items


def answer_question(question: str) -> ChatResponse:
    sources = retrieve(question, RETRIEVAL_TOP_K)
    prompt = build_prompt(sources)
    descriptions = generate(prompt)

    description_by_id = {item.id: item for item in descriptions}
    # 依檢索排名輸出；LLM 漏寫或寫錯編號的酒款就略過，不顯示沒有介紹的紀錄
    recommendations = []
    for source in sources:
        if source.id in description_by_id:
            item = description_by_id[source.id]
            recommendations.append(
                Recommendation(
                    title=source.title,
                    keywords=item.keywords,
                    description=item.description,
                    image=source.image,
                )
            )
    return ChatResponse(recommendations=recommendations)
