import re


def process_ocr_text(raw_text: str) -> str:
    # Убираем лишние пробелы и пустые строки
    lines = raw_text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        # Убираем строки из одних спецсимволов или слишком короткие
        line = re.sub(r"[^\w\s.,;:/()\-–+=%<>]", "", line)
        line = re.sub(r"\s{2,}", " ", line)
        if len(line) >= 2:
            cleaned.append(line)

    return "\n".join(cleaned)
