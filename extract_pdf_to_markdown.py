#!/usr/bin/env python3
"""Extract PDF into a single markdown file.
Usage: python extract_pdf_to_markdown.py <pdf_path> <output_dir>
"""

import sys
import os
import re
from pathlib import Path
import PyPDF2


def extract_pdf_text(pdf_path):
    """Extract all text from PDF."""
    text = ""
    with open(pdf_path, 'rb') as fp:
        pdf_reader = PyPDF2.PdfReader(fp)
        for page_num, page in enumerate(pdf_reader.pages):
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.extract_text()
    return text


def create_markdown_file(output_dir, filename, text):
    """Create a markdown file with the given text."""
    filepath = os.path.join(output_dir, filename)
    
    # Write file
    with open(filepath, 'w', encoding='utf-8') as fp:
        fp.write(text)
    
    print(f"Created: {filename}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_to_markdown.py <pdf_path> [output_dir]")
        print("Example: python extract_pdf_to_markdown.py src/files/2508.03680v1.pdf src/files")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'src/files'
    
    # Validate input
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Extracting PDF: {pdf_path}")
    
    # Extract text from PDF
    text = extract_pdf_text(pdf_path)
    print(f"Extracted {len(text)} characters from PDF")
    
    # Get PDF base name without extension
    pdf_name = Path(pdf_path).stem
    filename = f"{pdf_name}.md"
    
    # Create single markdown file
    create_markdown_file(output_dir, filename, text)
    
    print(f"\nSuccess! Created markdown file in {output_dir}")


if __name__ == '__main__':
    main()
