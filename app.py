import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, render_template
import pymupdf  # For PDF text extraction
import pytesseract  # For OCR
from PIL import Image  # For image handling

app = Flask(__name__)

german_stop_words = [
    "die", "der", "das", "ein", "eine", "und", "im", "in", "zu", "auf", "mit", "ist", "sind",
    "für", "an", "von", "sie", "den", "dem", "des", "am", "aus", "bei", "durch", "nach",
    "über", "unter", "vor", "zwischen", "bitte", "dank", "ihre", "ihren", "ihrer", "unser",
    "unsere", "nicht", "ab", "als", "wenden"
]

def analyze_text_similarity(csv_path, text_column):
    df = pd.read_csv(csv_path)
    df[text_column] = df[text_column].fillna("")
    tfidf_vectorizer = TfidfVectorizer(
        lowercase=True,
        analyzer='word',
        ngram_range=(1, 2),
        stop_words=german_stop_words
    )
    all_texts = df[text_column].tolist()
    tfidf_matrix = tfidf_vectorizer.fit_transform(all_texts)
    reference_vector = tfidf_matrix[0]
    tfidf_similarities = [cosine_similarity(reference_vector, tfidf_matrix[i])[0][0] for i in range(tfidf_matrix.shape[0])]
    df['tfidf_similarity'] = tfidf_similarities
    return df.sort_values('tfidf_similarity', ascending=False)

# Example OCR function
def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='deu')  # 'deu' for German
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

@app.route('/')
def index():
    # TF-IDF results
    result_df = analyze_text_similarity('german_dataset.csv', 'text')
    tfidf_results = result_df.to_dict('records')
    
    # Example OCR (replace with your image path if needed)
    ocr_text = extract_text_from_image('sample_image.png') if 'sample_image.png' in os.listdir() else "No image provided"
    
    return render_template('index.html', results=tfidf_results, ocr_text=ocr_text)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
