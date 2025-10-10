# PDF Parser - Extract text from resume

import pdfplumber

def extract_resume(uploaded_file):
    """
    Extract text from PDF resume
    Returns dict with text and word count
    """
    print("📄 Extracting resume from PDF...")
    
    try:
        text = ""
        
        # Read PDF with pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"   Reading page {page_num}...")
                page_text = page.extract_text(layout=True)
                if page_text:
                    text += page_text + "\n\n"
        
        # Clean up text
        text = text.strip()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        word_count = len(text.split())
        print(f"✓ Extracted {word_count} words")
        
        if word_count < 50:
            return {'success': False, 'error': 'Text too short - might be scanned PDF'}
        
        return {
            'success': True,
            'text': text,
            'word_count': word_count
        }
    
    except Exception as e:
        print(f"✗ Failed: {e}")
        return {'success': False, 'error': str(e)}