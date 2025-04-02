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
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# German stop words
german_stop_words = [
    "die", "der", "das", "ein", "eine", "und", "im", "in", "zu", "auf", "mit", "ist", "sind",
    "für", "an", "von", "sie", "den", "dem", "des", "am", "aus", "bei", "durch", "nach",
    "über", "unter", "vor", "zwischen", "bitte", "dank", "ihre", "ihren", "ihrer", "unser",
    "unsere", "nicht", "ab", "als", "wenden"
]

# --- PDF Processing ---
def pdf_to_text(pdf_file):
    try:
        pdf_document = fitz.Document(pdf_file)  # Updated from fitz.open
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

# --- Image OCR ---
def image_to_text(image_file):
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image, lang='deu')
        return text.strip()
    except Exception as e:
        return f"Error processing image: {str(e)}"

# --- Analyze Text Similarity ---
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

# --- Process File ---
def process_file(file):
    filename = secure_filename(file.filename)
    file_path = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)  # Ensure uploads directory exists
    file.save(file_path)
    
    if filename.lower().endswith('.pdf'):
        text = pdf_to_text(file_path)
    elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        text = image_to_text(file_path)
    else:
        text = "Unsupported file type"
    
    return text, filename

# --- Flask Routes ---
@app.route('/')
def index():
    session.pop('file1_text', None)  # Clear File 1 on refresh
    session.pop('file1_name', None)
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'file1' not in request.files or 'file2' not in request.files:
        return "Please upload both files!", 400
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if file1.filename == '' or file2.filename == '':
        return "Please select both files!", 400
    
    # Handle File 1 (persist if already uploaded)
    if 'file1_text' not in session:
        text1, file1_name = process_file(file1)
        session['file1_text'] = text1
        session['file1_name'] = file1_name
    else:
        text1 = session['file1_text']
        file1_name = session['file1_name']
    
    # Process File 2
    text2, file2_name = process_file(file2)
    
    # Analyze similarities
    df = analyze_text_similarity([text1, text2])
    tfidf_sim = df['tfidf_similarity'].iloc[1]
    
    return render_template('result.html', 
                          file1_name=file1_name, text1=text1[:500], 
                          file2_name=file2_name, text2=text2[:500],
                          tfidf_similarity=tfidf_sim)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
