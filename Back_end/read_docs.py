import os
from pypdf import PdfReader
from docx import Document

def read_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def read_docx(path):
    try:
        doc = Document(path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        return f"Error reading DOCX: {e}"

pdf_path = r"c:\Users\mompe\Desktop\EpiChat\IA bot Kick-off (2).pdf"
docx_path = r"c:\Users\mompe\Desktop\EpiChat\Documentation_HEPHAESTUS (1).docx"

print("--- PDF CONTENT ---")
print(read_pdf(pdf_path))
print("\n--- DOCX CONTENT ---")
print(read_docx(docx_path))
