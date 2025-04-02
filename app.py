import os
import pandas as pd
import fitz  # PyMuPDF
from flask import Flask, request, render_template, session
from PIL import Image
import pytesseract
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

german_stop_words = [
    "die", "der", "das", "ein", "eine", "und", "im", "in", "zu", "auf", "mit", "ist", "sind",
    "für", "an", "von", "sie", "den", "dem", "des", "am", "aus", "bei", "durch", "nach",
    "über", "unter", "vor", "zwischen", "bitte", "dank", "ihre", "ihren", "ihrer", "unser",
    "unsere", "nicht", "ab", "als", "wenden"
]

def pdf_to_text(pdf_file):
    try:
        pdf_document = fitz.Document(pdf_file)
        extracted_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text("text")
            if text:
                extracted_text += f"\n--- Page {page_num+1} ---\n" + text
        pdf_document.close()
        return extracted_text.strip()
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def image_to_text(image_file):
    try:
        image = Image.open(image_file)
        max_size = (1000, 1000)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        text = pytesseract.image_to_string(image, lang='deu', timeout=30)
        return text.strip()
    except pytesseract.TesseractTimeoutError:
        return "Error: Tesseract timed out while processing the image"
    except Exception as e:
        return f"Error processing image: {str(e)}"

def analyze_text_similarity(texts):
    df = pd.DataFrame({'text': texts})
    df['text'] = df['text'].fillna("")
    tfidf_vectorizer = TfidfVectorizer(
        lowercase=True,
        analyzer='word',
        ngram_range=(1, 2),
        stop_words=german_stop_words
    )
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['text'])
    reference_vector = tfidf_matrix[0]
    tfidf_similarities = [cosine_similarity(reference_vector, tfidf_matrix[i])[0][0] for i in range(tfidf_matrix.shape[0])]
    df['tfidf_similarity'] = tfidf_similarities
    return df

def process_file(file):
    filename = secure_filename(file.filename)
    file_path = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(file_path)
    
    if filename.lower().endswith('.pdf'):
        text = pdf_to_text(file_path)
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        text = image_to_text(file_path)
    else:
        text = "Unsupported file type"
    
    return text, filename

@app.route('/')
def index():
    session.pop('file1_text', None)
    session.pop('file1_name', None)
    return render_template('index.html')

@app.route('/test-tesseract')
def test_tesseract():
    try:
        version = pytesseract.get_tesseract_version()
        languages = pytesseract.get_languages()
        return f"Tesseract version: {version}<br>Available languages: {languages}"
    except Exception as e:
        return f"Tesseract error: {str(e)}"

@app.route('/submit', methods=['POST'])
def submit():
    if 'file1' not in request.files or 'file2' not in request.files:
        return "Please upload both files!", 400
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if file1.filename == '' or file2.filename == '':
        return "Please select both files!", 400
    
    if 'file1_text' in session:
        text1 = session['file1_text']
        file1_name = session['file1_name']
    else:
        text1, file1_name = process_file(file1)
        session['file1_text'] = text1
        session['file1_name'] = file1_name
    
    text2, file2_name = process_file(file2)
    
    df = analyze_text_similarity([text1, text2])
    tfidf_sim = df['tfidf_similarity'].iloc[1]
    
    return render_template('result.html', 
                          file1_name=file1_name, text1=text1[:500], 
                          file2_name=file2_name, text2=text2[:500],
                          tfidf_similarity=tfidf_sim)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
