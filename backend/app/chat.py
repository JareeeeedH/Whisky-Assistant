from app.schemas import ChatResponse, Source

# 假資料：資料庫檢索接上之前，先當作檢索結果
FAKE_SOURCES = [
    Source(
        id=1,
        title="Bunnahabhain 12 Year Old",
        source="fake://bunnahabhain-12",
        content="Bunnahabhain 位於艾雷島東北岸，主力酒款使用未經泥煤烘乾的麥芽，"
        "並以雪莉桶熟成為特色。",
    ),
    Source(
        id=2,
        title="Bruichladdich The Classic Laddie",
        source="fake://classic-laddie",
        content="The Classic Laddie 是 Bruichladdich 不使用泥煤的旗艦酒款，全部採用蘇格蘭大麥。",
    ),
]


def build_prompt(question: str, sources: list[Source]) -> str:
    raise NotImplementedError("由開發者實作：把問題和來源組成給 LLM 的 prompt")


def generate(prompt: str) -> str:
    # 暫時直接回傳 prompt：接上 LLM 之前，可以在前端畫面上檢查 build_prompt 組出來的內容
    return prompt


def answer_question(question: str) -> ChatResponse:
    sources = FAKE_SOURCES
    prompt = build_prompt(question, sources)
    answer = generate(prompt)
    return ChatResponse(answer=answer, sources=sources)
