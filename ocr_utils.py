import pytesseract
import re
from PIL import Image


def extract_text_from_image(image_path):
    """Extract raw text from image using Tesseract OCR."""
    return pytesseract.image_to_string(Image.open(image_path))


def extract_medications(text):
    """Extract medication names from OCR text."""
    meds = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if re.match(r"^(ASK|TAKE)?\s*(.*?)(\d+\s?mg|mcg|units|%|tab|capsule|cream|patch)?", line, re.IGNORECASE):
            if any(keyword in line.lower() for keyword in ["take", "tab", "capsule", "cream", "mcg", "mg"]):
                meds.append(line)
    return meds


def extract_allergies(text):
    """Extract allergy names and reactions from OCR text."""
    allergy_section = re.findall(r"Allergies\s*(continued)?(.*?)(Medications|Imaging|What's Next|\Z)", text, re.DOTALL | re.IGNORECASE)
    allergies = []
    for _, section, _ in allergy_section:
        for line in section.split('\n'):
            if line.strip():
                allergies.append(line.strip())
    return allergies


def summarize_ocr_results(image_path):
    """Run full OCR pipeline on image and extract useful summary."""
    raw_text = extract_text_from_image(image_path)
    meds = extract_medications(raw_text)
    allergies = extract_allergies(raw_text)
    return {
        "medications": meds,
        "allergies": allergies,
        "raw_text": raw_text
    }
