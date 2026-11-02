from app.schemas import ChatResponse, Source

# 假資料：RAG 接上之前，先用來串通前後端
FAKE_ANSWER = (
    "如果想找泥煤味不重的艾雷島威士忌，可以從這兩支開始：\n\n"
    "- **Bunnahabhain 12**：使用幾乎不帶泥煤的麥芽，雪莉桶帶來果乾與堅果香氣 [1]。\n"
    "- **Bruichladdich The Classic Laddie**：完全不使用泥煤，"
    "風味以大麥本身的甜感和花香為主 [2]。\n\n"
    "（這是開發用的假資料，尚未接上知識庫。）"
)

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


def answer_question(question: str) -> ChatResponse:
    return ChatResponse(answer=FAKE_ANSWER, sources=FAKE_SOURCES)
