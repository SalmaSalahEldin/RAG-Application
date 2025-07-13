#!/bin/bash

# Setup script for advanced PDF processing with OCR capabilities
# This script installs all necessary system dependencies and Python packages

set -e

echo "Setting up advanced PDF processing with OCR capabilities..."

# Check if running on Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    echo "Installing system dependencies (Ubuntu/Debian)..."
    sudo apt-get update
    sudo apt-get install -y \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-fra \
        tesseract-ocr-deu \
        tesseract-ocr-spa \
        libtesseract-dev \
        poppler-utils \
        python3-dev \
        python3-pip \
        build-essential

# Check if running on macOS
elif command -v brew &> /dev/null; then
    echo "Installing system dependencies (macOS)..."
    brew install tesseract
    brew install poppler

# Check if running on CentOS/RHEL/Fedora
elif command -v yum &> /dev/null; then
    echo "Installing system dependencies (CentOS/RHEL/Fedora)..."
    sudo yum install -y \
        tesseract \
        tesseract-langpack-eng \
        poppler-utils \
        python3-devel \
        gcc \
        gcc-c++

else
    echo "Unsupported operating system. Please install tesseract and poppler manually."
    echo "Required packages: tesseract-ocr, poppler-utils"
fi

echo "Installing Python packages..."

# Install the enhanced requirements
pip install --upgrade pip

# Core packages
pip install \
    fastapi==0.110.2 \
    uvicorn[standard]==0.29.0 \
    python-multipart==0.0.9 \
    python-dotenv==1.0.1 \
    pydantic-settings==2.2.1 \
    aiofiles==23.2.1 \
    langchain==0.1.20 \
    PyMuPDF==1.24.3

# Advanced PDF processing packages
pip install \
    "unstructured[pdf]==0.15.13" \
    pytesseract==0.3.13 \
    pdf2image==1.17.0 \
    pillow==10.4.0 \
    pdfplumber==0.11.4 \
    tabula-py==2.9.3

# Optional: Additional OCR engines
echo "Do you want to install additional OCR engines? (y/n)"
read -r install_additional

if [[ $install_additional == "y" || $install_additional == "Y" ]]; then
    pip install easyocr paddlepaddle paddleocr
fi

echo ""
echo "Setup complete!"
echo ""
echo "You can now use the smart PDF processing capabilities:"
echo "1. Basic usage with unstructured library (recommended)"
echo "2. Custom hybrid approach for specific needs"
echo "3. Content-aware processing for complex documents"
echo ""
echo "Test your setup with:"
echo "python src/examples/smart_pdf_example.py <your_pdf_file>"
echo ""
echo "Dependencies installed:"
echo "- Tesseract OCR for text recognition"
echo "- Poppler for PDF to image conversion"
echo "- PyMuPDF for PDF manipulation"
echo "- pdfplumber for table detection"
echo "- unstructured for intelligent document processing" 