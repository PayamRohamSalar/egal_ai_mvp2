# src/utils/text_utils.py
"""
Persian text processing utilities for Legal Assistant
Handles Persian-specific text cleaning, normalization, and analysis
"""

import re
from typing import Dict, List, Tuple, Optional
import unicodedata

class PersianTextProcessor:
    """Persian text processing utilities"""
    
    def __init__(self):
        # Persian-Arabic character normalization mapping
        self.char_map = {
            'ك': 'ک', 'ي': 'ی', 'ء': 'ئ', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
            'ة': 'ه', 'ؤ': 'و', 'ئ': 'ی', '٠': '۰', '١': '۱', '٢': '۲',
            '٣': '۳', '٤': '۴', '٥': '۵', '٦': '۶', '٧': '۷', '٨': '۸', '٩': '۹'
        }
        
        # Persian digits mapping
        self.persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        self.english_to_persian = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
        
        # Common Persian legal terms for keyword extraction
        self.legal_keywords = {
            'قانون', 'آیین‌نامه', 'دستورالعمل', 'مصوبه', 'بخشنامه',
            'ماده', 'تبصره', 'بند', 'فصل', 'قسمت', 'بخش',
            'مجلس', 'شورای', 'وزیر', 'رئیس‌جمهور', 'هیئت‌وزیران',
            'تصویب', 'ابلاغ', 'اجرا', 'لغو', 'اصلاح', 'الحاق'
        }

    def normalize_persian_text(self, text: str) -> str:
        """
        Normalize Persian text by standardizing characters
        
        Args:
            text (str): Input Persian text
            
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
        
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Character-level normalization
        for old_char, new_char in self.char_map.items():
            text = text.replace(old_char, new_char)
        
        return text

    def clean_text(self, text: str) -> str:
        """
        Clean and standardize Persian text
        
        Args:
            text (str): Raw text input
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Normalize characters first
        text = self.normalize_persian_text(text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix punctuation spacing (Persian style)
        text = re.sub(r'\s*([،؛؟!.])\s*', r'\1 ', text)
        text = re.sub(r'\s*([()])\s*', r' \1 ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text

    def extract_persian_numbers(self, text: str) -> List[str]:
        """
        Extract Persian numbers from text
        
        Args:
            text (str): Input text
            
        Returns:
            List[str]: List of found Persian numbers
        """
        pattern = r'[۰-۹]+(?:[./][۰-۹]+)*'
        return re.findall(pattern, text)

    def convert_persian_to_english_digits(self, text: str) -> str:
        """
        Convert Persian digits to English digits
        
        Args:
            text (str): Text with Persian digits
            
        Returns:
            str: Text with English digits
        """
        return text.translate(self.persian_to_english)

    def convert_english_to_persian_digits(self, text: str) -> str:
        """
        Convert English digits to Persian digits
        
        Args:
            text (str): Text with English digits
            
        Returns:
            str: Text with Persian digits
        """
        return text.translate(self.english_to_persian)

    def extract_dates(self, text: str) -> List[Dict[str, str]]:
        """
        Extract Persian dates from text
        
        Args:
            text (str): Input text
            
        Returns:
            List[Dict]: List of date dictionaries with 'date' and 'format' keys
        """
        dates = []
        
        # Persian date patterns
        patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'dd/mm/yyyy'),
            (r'(\d{1,2})/(\d{1,2})/(\d{2})', 'dd/mm/yy'),
            (r'([۰-۹]{1,2})/([۰-۹]{1,2})/([۰-۹]{4})', 'persian_dd/mm/yyyy'),
            (r'([۰-۹]{1,2})/([۰-۹]{1,2})/([۰-۹]{2})', 'persian_dd/mm/yy'),
        ]
        
        for pattern, date_format in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                date_str = '/'.join(match)
                dates.append({'date': date_str, 'format': date_format})
        
        return dates

    def extract_keywords(self, text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
        """
        Extract Persian keywords from legal text
        
        Args:
            text (str): Input text
            min_length (int): Minimum keyword length
            max_keywords (int): Maximum number of keywords to return
            
        Returns:
            List[str]: List of extracted keywords
        """
        if not text:
            return []
        
        # Clean text first
        cleaned_text = self.clean_text(text)
        
        # Split into words
        words = re.findall(r'[\u0600-\u06FF\u200C\u200D]+', cleaned_text)
        
        # Filter and score keywords
        keyword_scores = {}
        
        for word in words:
            if len(word) >= min_length:
                # Higher score for legal terms
                score = 2 if word in self.legal_keywords else 1
                keyword_scores[word] = keyword_scores.get(word, 0) + score
        
        # Sort by score and return top keywords
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:max_keywords]]

    def is_valid_persian_text(self, text: str) -> bool:
        """
        Check if text contains valid Persian content
        
        Args:
            text (str): Text to validate
            
        Returns:
            bool: True if text contains Persian characters
        """
        if not text or len(text.strip()) < 3:
            return False
        
        # Check for Persian characters
        persian_char_count = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'[\w]', text))
        
        if total_chars == 0:
            return False
        
        # At least 30% should be Persian characters
        persian_ratio = persian_char_count / total_chars
        return persian_ratio >= 0.3

    def split_sentences(self, text: str) -> List[str]:
        """
        Split Persian text into sentences
        
        Args:
            text (str): Input text
            
        Returns:
            List[str]: List of sentences
        """
        if not text:
            return []
        
        # Persian sentence boundary markers
        sentence_pattern = r'[.؟!؛]\s+'
        sentences = re.split(sentence_pattern, text.strip())
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences

    def extract_legal_references(self, text: str) -> List[Dict[str, str]]:
        """
        Extract legal references like article numbers, notes, etc.
        
        Args:
            text (str): Input text
            
        Returns:
            List[Dict]: List of legal references
        """
        references = []
        
        # Patterns for legal references
        patterns = [
            (r'(ماده\s*[۰-۹]+)', 'article'),
            (r'(تبصره\s*[۰-۹]*)', 'note'),
            (r'(بند\s*[۰-۹]+)', 'subsection'),
            (r'(فصل\s*[۰-۹]+)', 'chapter'),
            (r'(قانون\s+[^.،؛]+)', 'law_reference'),
        ]
        
        for pattern, ref_type in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                references.append({
                    'text': match,
                    'type': ref_type,
                    'position': text.find(match)
                })
        
        return references

# Utility functions for standalone use
def clean_persian_text(text: str) -> str:
    """Standalone function to clean Persian text"""
    processor = PersianTextProcessor()
    return processor.clean_text(text)

def extract_persian_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Standalone function to extract Persian keywords"""
    processor = PersianTextProcessor()
    return processor.extract_keywords(text, max_keywords=max_keywords)

def normalize_text(text: str) -> str:
    """Standalone function to normalize Persian text"""
    processor = PersianTextProcessor()
    return processor.normalize_persian_text(text)

# Test the utility functions
if __name__ == "__main__":
    # Test with sample Persian legal text
    sample_text = """
    قانون مقررات انتظامی هیئت علمی (مصوب ۲۲/۱۲/۱۳۶۴)
    ماده ۱ - هیئت علمی دانشگاه‌ها موظف به رعایت مقررات این قانون هستند.
    تبصره: این ماده شامل تمام اعضای هیئت علمی می‌شود.
    """
    
    processor = PersianTextProcessor()
    
    print("متن اصلی:")
    print(sample_text)
    print("\nمتن تمیز شده:")
    print(processor.clean_text(sample_text))
    print("\nکلیدواژه‌های استخراج شده:")
    print(processor.extract_keywords(sample_text))
    print("\nارجاعات حقوقی:")
    print(processor.extract_legal_references(sample_text))