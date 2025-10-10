# Web Scraper - Get job description from URL

from langchain_community.document_loaders import WebBaseLoader
import requests
from bs4 import BeautifulSoup

def fetch_job(job_url):
    """
    Fetch job description from URL
    Returns dict with text and word count
    """
    print("🌐 Fetching job description...")
    
    try:
        # Method 1: Try LangChain WebBaseLoader
        try:
            print("   Trying WebBaseLoader...")
            loader = WebBaseLoader(job_url)
            docs = loader.load()
            job_text = docs[0].page_content
            
        except Exception as e1:
            print(f"   WebBaseLoader failed: {e1}")
            print("   Trying BeautifulSoup fallback...")
            
            # Method 2: Fallback to requests + BeautifulSoup
            response = requests.get(job_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            job_text = soup.get_text()
        
        # Clean the text
        lines = [line.strip() for line in job_text.split('\n') if line.strip()]
        
        # Remove common junk
        unwanted = ['cookie policy', 'privacy policy', 'apply now', 
                   'sign in', 'share this job', 'save job']
        clean_lines = []
        for line in lines:
            if not any(junk in line.lower() for junk in unwanted):
                clean_lines.append(line)
        
        job_text = '\n'.join(clean_lines)
        word_count = len(job_text.split())
        
        print(f"✓ Fetched {word_count} words")
        
        if word_count < 50:
            return {'success': False, 'error': 'Description too short'}
        
        return {
            'success': True,
            'text': job_text,
            'word_count': word_count
        }
    
    except Exception as e:
        print(f"✗ Failed: {e}")
        return {'success': False, 'error': str(e)}