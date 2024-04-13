'''
ocr

This module is used to convert PDF-Papers into images, so that their content can be extarcted
utilising OCR.
'''

from pdf2image import convert_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'' # Path to tesseract.exe
POPPLER_PATH = r'' # Path to the poppler binary file needed for pdf2image

def convert_to_txt(p_input_file, p_output_file):
    '''
    Extracts PDF-File content and writes it into a TXT-File.

    Args:
        p_input_file (String): PDF-File to be converted.
        p_output_file (String):  TXT-File to be written into.
    '''

    # Convert each page of the PDF into an image.
    images = convert_from_path(p_input_file, poppler_path=POPPLER_PATH, dpi=200)

    # Remove prior content of output TXT-File.
    with open(p_output_file, 'w', encoding='utf-8') as file:
        pass

    # Extract text from each image via OCR and append the text to the output TXT-File.
    with open(p_output_file, 'a', encoding='utf-8') as file:
        for image in images:
            text = pytesseract.image_to_string(image, lang='eng')
            file.write(f"{text}\n")
