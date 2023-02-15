# Requires Python 3.6 or higher due to f-strings
 
# Import libraries
import platform
from tempfile import TemporaryDirectory
from pathlib import Path
 
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
 
import re
import os

import spacy

CONTENT_LEGNTH_BUFFER = 8 # Assume content is at least 8 lines

def pdftotxt(pdf_filename, out_txt_filename, progress_updates = False):
    
    if platform.system() == "Windows":
        # We may need to do some additional downloading and setup...
        # Windows needs a PyTesseract Download
        # https://github.com/UB-Mannheim/tesseract/wiki/Downloading-Tesseract-OCR-Engine
    
        path_to_tesseract_exe = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        pytesseract.pytesseract.tesseract_cmd = (path_to_tesseract_exe)
    
        # Windows also needs poppler_exe: path_to_poppler_exe = Path(r"...")
        # As 2023, oschwartz keeps the poppler-windows repository fairly up to date
        # https://github.com/oschwartz10612/poppler-windows/releases
        path_to_poppler_exe = Path(r"C:\Users\ccard\Freelance\Word Embedding Project\Release-23.01.0-0\poppler-23.01.0\Library\bin")
        
        # Put our output files in a sane place...
        out_directory = Path("").expanduser()
    else:
        out_directory = Path("").expanduser()    
    
    # Path of the Input pdf
    PDF_file = Path(r"{}".format(pdf_filename))
    
    # Store all the pages of the PDF in a variable
    image_file_list = []
    
    text_file = out_directory / Path(r"{}".format(out_txt_filename))

    ''' Main execution point of the program'''
    
    with TemporaryDirectory() as tempdir:
        # Create a temporary directory to hold our temporary images.
 
        """
        Part #1 : Converting PDF to images
        """
 
        if platform.system() == "Windows":
            pdf_pages = convert_from_path(
                PDF_file, 500, poppler_path=path_to_poppler_exe, thread_count = 16
            )
        else:
            pdf_pages = convert_from_path(PDF_file, 500)
        # Read in the PDF file at 500 DPI
 
        # Iterate through all the pages stored above
        for page_enumeration, page in enumerate(pdf_pages, start=1):
            # enumerate() "counts" the pages for us.

            if progress_updates:
                print("Saving pdf pages to  high resolution jpeg format\n", "Currently on page:")
                if page_enumeration % 10 == 0:
                    print(page_enumeration)

            # Create a file name to store the image
            filename = f"{tempdir}\page_{page_enumeration:03}.jpg"
 
            # Declaring filename for each page of PDF as JPG
            # For each page, filename will be:
            # PDF page 1 -> page_001.jpg
            # PDF page 2 -> page_002.jpg
            # PDF page 3 -> page_003.jpg
            # ....
            # PDF page n -> page_00n.jpg
 
            # Save the image of the page in system
            page.save(filename, "JPEG")
            image_file_list.append(filename)
        
        if progress_updates:
            print("Finished PDF to JPEG")

        """
        Part #2 - Recognizing text from the images using OCR
        """
 
        with open(text_file, "w") as output_file:
            # Open the file in append mode so that
            # All contents of all images are added to the same file
 
            # Iterate from 1 to total number of pages
            count = 0
            for image_file in image_file_list:
 
                # Set filename to recognize text from
                # Again, these files will be:
                # page_1.jpg
                # page_2.jpg
                # ....
                # page_n.jpg

                if progress_updates:
                    print("Performing OCR on images\n", "Currently on page:")
                    if count % 10 == 0:
                        print(count)
                    count += 1

                # Recognize the text as string in image using pytesserct
                text = str(((pytesseract.image_to_string(Image.open(image_file)))))
 
                # The recognized text is stored in variable text
                # Any string processing may be applied on text
                # Here, basic formatting has been done:
                # In many PDFs, at line ending, if a word can't
                # be written fully, a 'hyphen' is added.
                # The rest of the word is written in the next line
                # To remove this, we replace every '-\n' to ''.
                text = text.replace("-\n", "")
 
                # Finally, write the processed text to the file.
                output_file.write(text)
 
            # At the end of the with .. output_file block
            # the file is closed after writing all the text.
        # At the end of the with .. tempdir block, the
        # TemporaryDirectory() we're using gets removed!

        if progress_updates:
            print("Finished OCR on JPEG")

def contains_year(string, year_min, year_max):
    year_pattern = f"([{year_min}-{year_max}])"
    match = re.search(year_pattern, string)
    if match:
        return True
    else:
        return False
    
def chunk_parse_namebased(chunk):
    
    nlp = spacy.load("en_core_web_sm")
    
    for key, line in enumerate(chunk[:-1]):
        
        # Fixes M.M.Mulokozi -> M. M. Mulokozi
        # MM.Mulokozi -> M. M. Mulokozi
        if chunk[key-1] == "\n" and chunk[key+1] == "\n":
            
            line = [i.strip() for i in line.split(".")]
            if len(line) >= 3:
                line = ". ".join(line)
            elif len(line) == 1:
                line = line[0]
            elif len(line) == 2:
                if len(line[0]) > 3 and len(line[1]) > 3:
                    line = ". ".join(line)
                else:
                    for i in range(len(line)):
                        if len(line[i]) < 3 and i < len(line)-1:
                            line[i] = "".join([x + ". " for x in line[i]])
                    line = " ".join(line)
            

        # Detects split based on foreward named sign-off
        doc = nlp(line)
        contains_person_name = False
        for entity in doc.ents:
            
            if entity.label_ == "PERSON":
                contains_person_name = True
    
        if chunk[key-1] == "\n" and chunk[key+1] == "\n":
            if contains_person_name and key < len(chunk) - CONTENT_LEGNTH_BUFFER:
                chunk_foreward = chunk[:key+1]
                chunk_content = chunk[key+1:]
                return chunk_foreward, chunk_content
    
    return "FAILURE", "FAILURE"

def chunk_parse_newlinebased(chunk):
    
    for key, line in enumerate(chunk[:-1]):
        if "\n" in line and len(line < 6):
            chunk[key] = "\n"
    
    for key, line in enumerate(chunk[2:-1*CONTENT_LEGNTH_BUFFER]):
        if chunk[key-1] == "\n" and chunk[key] == "\n" and chunk[key+1] == "\n":
            chunk_foreward = chunk[:key+1]
            chunk_content = chunk[key+1:]
            return chunk_foreward, chunk_content
    
    return "FAILURE", "FAILURE"
