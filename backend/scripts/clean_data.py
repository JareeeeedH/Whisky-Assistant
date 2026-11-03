"""清理原始品飲筆記，輸出 data/whisky_clean.json 給匯入腳本使用。

清理規則見 SPEC.md 第 6 節。原始檔不會被修改，規則調整後重跑即可。
"""

import html
import json
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_PATH = DATA_DIR / "whiskyDataset.json"
CLEAN_PATH = DATA_DIR / "whisky_clean.json"
# 被排除的資料連同原因另存一份，方便人工檢查篩選規則有沒有誤刪
EXCLUDED_PATH = DATA_DIR / "whisky_excluded.json"

# 酒名括號內以逗號分隔的項目若「整項」等於下列任一詞，就視為非威士忌。
# 只比對整項，`rum cask finish` 這類過桶描述才不會被誤刪
OTHER_SPIRITS = {
    "rum", "rhum", "agricole", "rhum agricole", "tequila", "mezcal", "raicilla", "sotol",
    "cognac", "armagnac", "bas-armagnac", "haut-armagnac", "ténarèze", "tenareze",
    "grande champagne", "petite champagne", "fine champagne", "borderies", "fins bois",
    "bons bois", "calvados", "pommeau", "brandy", "eau-de-vie", "grappa", "pisco",
    "cachaca", "cachaça", "gin", "vodka", "baijiu", "arrack", "liqueur",
}  # fmt: skip

# 很多蘭姆酒的酒名只寫產地、不寫 rum，所以產地也要比對
OTHER_SPIRIT_PLACES = {
    "barbados", "jamaica", "guyana", "demerara", "martinique", "guadeloupe", "marie-galante",
    "trinidad", "haiti", "panama", "venezuela", "mauritius", "cuba", "dominican republic",
    "fiji", "reunion", "réunion", "nicaragua", "guatemala", "belize", "grenada", "st lucia",
    "saint lucia", "antigua", "puerto rico", "philippines", "mexico", "colombia", "peru",
    "bolivia", "brazil", "guadalajara", "jalisco", "oaxaca", "ecuador", "madagascar",
}  # fmt: skip

# 段落標籤前的空白換成換行，讓 LLM 和前端都能看出段落；沒照格式寫的筆記只是少換幾行
SECTION_BREAK = re.compile(
    r" (?=(?:Colou?r|Nose|Mouth|Palate|With water|Finish|Comments?)(?: \([^)]{1,30}\))?:)"
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def brand_of(name: str) -> str:
    # 酒名開頭到第一個數字、引號或括號之前，例如 `Hampden 8 yo (...)` → `hampden`
    return re.split(r"\s+(?=\d|['‘’\"“(])|\s*\(", name, maxsplit=1)[0].strip().lower()


def other_spirit_match(name: str) -> str | None:
    # 回傳判定為非威士忌的依據（比對到的詞），寫進排除清單方便人工檢查；是威士忌則回傳 None
    # 有些蘭姆酒、干邑直接以產地或類別當酒名，例如 `Jamaica 1990 (...)`
    brand = brand_of(name).removeprefix("la ")
    if brand in OTHER_SPIRITS or brand in OTHER_SPIRIT_PLACES:
        return brand
    if re.search(r"\b(rum|rhum)\b", brand):
        return brand
    for group in re.findall(r"\(([^()]*)\)", name):
        for item in group.split(","):
            item = item.strip().lower().removeprefix("la ")
            if item in OTHER_SPIRITS or item in OTHER_SPIRIT_PLACES:
                return item
            # 排除含 whisky 的項目：法國獨立裝瓶商就叫 `Whisky & Rhum`
            if re.search(r"\brhum\b", item) and "whisky" not in item:
                return item
    return None


def other_spirit_brands(names: list[str]) -> set[str]:
    # 很多蘭姆酒、干邑的酒名只寫酒廠名（如 `Hampden 8 yo (56.5%, Kintra)`），單筆看不出來；
    # 同品牌有 10% 以上被判定為非威士忌時，整個品牌都排除。
    # 實測非威士忌品牌至少 14%，威士忌酒廠因特例被誤判的最多約 6%（如 Kavalan 101 筆中 1 筆）
    flagged: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for name in names:
        brand = brand_of(name)
        total[brand] += 1
        if other_spirit_match(name) is not None:
            flagged[brand] += 1
    return {brand for brand in flagged if flagged[brand] / total[brand] >= 0.1}


def parse_points(score: str) -> int | None:
    # 多位評審的寫法（OH 92 DB 88 SV 91 points）只會比對到緊貼 points 的最後一個分數
    match = re.search(r"(\d+)\s*points", score)
    if match is None:
        return None
    return int(match.group(1))


def parse_sgp(score: str) -> str | None:
    # SGP 固定是三位數；SGP:??? 或位數不對的都當成沒有
    match = re.search(r"SGP\s*:?\s*(\d{3})\b", score)
    if match is None:
        return None
    return match.group(1)


def main() -> None:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    other_brands = other_spirit_brands([normalize(record["NAME"]) for record in raw])

    cleaned: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    for record in raw:
        name = normalize(record["NAME"])
        note = SECTION_BREAK.sub("\n", normalize(record["NOTE"]))

        reason = None
        matched = None
        # 沒有括號的「酒名」其實是一句話，無法辨識是哪支酒
        if "(" not in name:
            reason = "酒名是一句話"
        elif (matched := other_spirit_match(name)) is not None:
            reason = "非威士忌烈酒"
        elif brand_of(name) in other_brands:
            reason = "非威士忌烈酒（同品牌推斷）"
            matched = brand_of(name)

        if reason is not None:
            excluded.append(
                {
                    "id": record["id"],
                    "name": name,
                    "reason": reason,
                    "matched": matched,
                    "note": note,
                }
            )
            continue

        score = normalize(record["SCORE"])
        cleaned.append(
            {
                "id": record["id"],
                "name": name,
                "note": note,
                "points": parse_points(score),
                "sgp": parse_sgp(score),
                # 只留檔名：圖片庫不沿用原始的 MaterialNN 資料夾，前端依檔名組出網址
                "image": record["IMAGE_PATH"].split("/")[-1],
            }
        )

    CLEAN_PATH.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
    EXCLUDED_PATH.write_text(json.dumps(excluded, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"原始：{len(raw)} 筆")
    for reason, count in Counter(r["reason"] for r in excluded).items():
        print(f"排除（{reason}）：{count} 筆")
    print(f"排除清單 → {EXCLUDED_PATH}")
    print(f"保留：{len(cleaned)} 筆 → {CLEAN_PATH}")
    print(f"points 解析不到：{sum(r['points'] is None for r in cleaned)} 筆")
    print(f"sgp 解析不到：{sum(r['sgp'] is None for r in cleaned)} 筆")


if __name__ == "__main__":
    main()
