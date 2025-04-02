FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

# Install other dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PyMuPDF last to ensure the correct version
RUN pip install --no-cache-dir PyMuPDF==1.24.2

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
