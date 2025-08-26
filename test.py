import time
from docling.document_converter import DocumentConverter
from pdf2image import convert_from_path
import pytesseract
from pdf_orientation_corrector import detect_and_correct_orientation

def docling_test(source):
    start_time = time.time()

    #converter = DocumentConverter(source=source, target="json", output_dir="C:/Users/Zaphare/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG")
    converter = DocumentConverter()

    result = converter.convert(source)
    print(result.document.export_to_markdown())

    # print("TEXT: ")
    # print(result.document.export_to_text())

    end_time = time.time()
    print(f"Document conversion took {end_time - start_time:.2f} seconds")   

def nltk_test():
    from nltk.tokenize import sent_tokenize, word_tokenize
    import nltk
    nltk.download('punkt_tab')

    text = open("test_data_kgg1.txt", "r", encoding="utf-8").read()
    sentences = sent_tokenize(text)

    for index, sentence in enumerate(sentences):
        print(f"Sentence: {sentence}")
        words = word_tokenize(sentence)
        print(f"Words: {words}")

def rotation_test():
    from pypdf import PdfReader
    reader = PdfReader('testpdf.pdf')

    counter = 0
    for page in reader.pages:
        rotation = page.get('/Rotate')
        counter += 1
        print(f"Rotation of page {counter}: {rotation} degrees")

def extraction_test():
    from pypdf import PdfReader

    reader = PdfReader('testpdf.pdf')
    for page in reader.pages:
        text = page.extract_text()
        print(f"Text from page {reader.pages.index(page) + 1}: {text}")

def extraction_ocr():
    poppler_path = "C:\\test\\poppler\\poppler-24.08.0\\Library\\bin"
    images = convert_from_path('testpdf.pdf', poppler_path=poppler_path)

    # for i, image in enumerate(images):
    #     text = pytesseract.image_to_string(image)
    #     print(f"Text from page {i + 1} (OCR): {text}")

    # safe images to disk
    for i, image in enumerate(images):
        image.save(f"page_{i + 1}.png", "PNG")

def rotation_with_module():
    detect_and_correct_orientation(pdf_path="testpdf.pdf", output_path="corrected_testpdf.pdf")

def corrected_to_text():
    # converse corrected pdf to images
    poppler_path = "C:\\test\\poppler\\poppler-24.08.0\\Library\\bin"
    images = convert_from_path('corrected_testpdf.pdf', poppler_path=poppler_path)

    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        print(f"Text from page {i + 1} (OCR): {text}")

def full_conversion_flow(input_pdf):
    output_path = "corrected_" + input_pdf
    detect_and_correct_orientation(pdf_path=input_pdf, output_path=output_path)

    poppler_path = "C:\\test\\poppler\\poppler-24.08.0\\Library\\bin"
    images = convert_from_path(output_path, poppler_path=poppler_path)

    full_text = ""

    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        print(f"Text from page {i + 1} (OCR): {text}")
        full_text += text + "\n\n\n"

    # could try to classify the document based on the structure/information available

    # retrieve text between "Relevante Diagnosen:" and "Rehabilitationsziel / Bemerkungen"
    
    if "Relevante Diagnosen" in full_text:
        relevant_diagnoses = full_text.split("Relevante Diagnosen:")[1].split("Rehabilitationsziel / Bemerkungen")[0]
        print(f"Relevant Diagnoses: {relevant_diagnoses}")
    elif "Hauptdiagnose" in full_text:
        main_diagnosis = full_text.split("Hauptdiagnose:")[1].split("Operation / Datum / Therapie")[0]
        print(f"----- Main Diagnosis: {main_diagnosis}")

# def combine_docling_and_tesseract(pdf_path):
#     from docling.datamodel.base_models import InputFormat
#     from docling.datamodel.pipeline_options import (
#         PdfPipelineOptions,
#         TesseractCliOcrOptions,
#     )
#     from docling.document_converter import DocumentConverter, PdfFormatOption

#     pipeline_options = PdfPipelineOptions()
#     pipeline_options.do_ocr = True
#     pipeline_options.ocr_options = TesseractCliOcrOptions(path="C:\\Program Files\\Tesseract-OCR\\tesseract.exe")  # Use Tesseract


#     converter = DocumentConverter(
#         format_options={
#             InputFormat.PDF: PdfFormatOption(
#                 pipeline_options=pipeline_options,
#             )
#         }
#     )

#     doc = converter.convert(pdf_path).document
#     md = doc.export_to_markdown()
#     print(md)


if __name__ == "__main__":
    # docling_test("C:/Users/Zaphare/OneDrive - FHNW/0_MSC/0_Thesis/Research_Papers/KGG/KGG_6.pdf")
    # nltk_test()
    # rotation_test()
    
    # rotation_with_module()
    # docling_test("corrected_testpdf.pdf")

    # full_conversion_flow("testpdf3.pdf")
    combine_docling_and_tesseract("testpdf3.pdf")