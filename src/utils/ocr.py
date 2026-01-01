import pytesseract
import logging

logger = logging.getLogger("document_ocr")
logger.setLevel(logging.INFO)

def analyze_text_confidence(text: str) -> float:
    if not text:
        return 0.0

    words = text.split()
    if not words:
        return 0.0

    avg_word_len = sum(len(w) for w in words) / len(words)

    score = 0
    if len(text) > 300:
        score += 0.4
    if avg_word_len > 3:
        score += 0.4
    if len(words) > 80:
        score += 0.2

    return round(score, 2)

def ocr_page_image(page_image, page_no: int) -> str:
    text = pytesseract.image_to_string(page_image, lang="eng")

    text = text.replace("\x00", "")
    
    if text.strip():
        logger.info(f"[OCR] Page {page_no}: OCR text extracted")
        return f"\n--- OCR Page {page_no} ---\n{text}"
    return ""