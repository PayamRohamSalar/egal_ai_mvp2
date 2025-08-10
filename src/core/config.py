# src/core/config.py
"""
Core configuration settings for Legal Assistant AI
Manages all system-wide configurations and constants
"""

from pathlib import Path
from typing import Dict, List
import os

# Project structure configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
SRC_DIR = PROJECT_ROOT / "src"

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, SAMPLE_DATA_DIR]:
    directory.mkdir(exist_ok=True)

# Document processing configuration
DOCUMENT_CONFIG = {
    # File settings
    "input_file": "Part2_Legals.docx",
    "encoding": "utf-8",
    
    # Legal document patterns (Persian)
    "law_separator": r"\*{10,}",  # 10 or more asterisks
    "law_title_pattern": r"^(.+?)\s*\(مصوب\s+(.+?)\)$",
    "chapter_pattern": r"^(فصل\s+[^\s]+)\s*[-–—]?\s*(.*)$",
    "article_pattern": r"^(ماده\s*[^\s]+)\s*[-–—]?\s*(.*)$",
    "single_article_pattern": r"^(ماده\s*واحده)\s*[-–—]?\s*(.*)$",
    "subsection_pattern": r"^([^\s]*\s*[-–—]\s*.*)$",
    "note_pattern": r"^(تبصره\s*[^\s]*)\s*[-–—]?\s*(.*)$",
    "footnote_pattern": r"^\(\d+\)",
    
    # Text processing
    "min_chunk_size": 200,
    "max_chunk_size": 1000,
    "chunk_overlap": 100,
    "persian_digits": "۰۱۲۳۴۵۶۷۸۹",
    "english_digits": "0123456789",
}

# Text cleaning configuration
TEXT_CLEANING = {
    # Characters to normalize
    "normalize_chars": {
        "ك": "ک",
        "ي": "ی",
        "ء": "ئ",
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
    },
    
    # Whitespace normalization
    "normalize_whitespace": True,
    "remove_extra_spaces": True,
    
    # Punctuation standardization
    "standardize_punctuation": {
        "،": "،",
        "؛": "؛",
        "؟": "؟",
        "!": "!",
        ".": ".",
    }
}

# Metadata extraction configuration
METADATA_CONFIG = {
    "extract_keywords": True,
    "extract_dates": True,
    "extract_authorities": True,
    "keyword_min_length": 3,
    "max_keywords_per_document": 20,
}

# Output file configuration
OUTPUT_FILES = {
    "individual_laws": PROCESSED_DATA_DIR / "individual_laws.json",
    "processed_documents": PROCESSED_DATA_DIR / "documents.json",
    "metadata": PROCESSED_DATA_DIR / "metadata.json",
    "chunks": PROCESSED_DATA_DIR / "chunks.json",
    "processing_report": PROCESSED_DATA_DIR / "processing_report.json",
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": PROJECT_ROOT / "logs" / "legal_assistant.log",
}

# Persian language specific settings
PERSIAN_CONFIG = {
    "rtl_support": True,
    "persian_calendar": True,
    "persian_numbers": True,
    "common_legal_terms": [
        "قانون", "آیین‌نامه", "دستورالعمل", "مصوبه", "بخشنامه",
        "ماده", "تبصره", "بند", "فصل", "قسمت", "بخش",
        "مجلس", "شورای", "وزیر", "رئیس‌جمهور", "هیئت‌وزیران",
        "تصویب", "ابلاغ", "اجرا", "لغو", "اصلاح"
    ],
}

# Quality assurance settings
QUALITY_ASSURANCE = {
    "min_law_length": 50,  # Minimum characters for a valid law
    "max_laws_expected": 50,  # Maximum number of laws expected
    "validate_structure": True,
    "check_completeness": True,
}

def get_config() -> Dict:
    """
    Get complete configuration dictionary
    
    Returns:
        Dict: Complete configuration settings
    """
    return {
        "document": DOCUMENT_CONFIG,
        "text_cleaning": TEXT_CLEANING,
        "metadata": METADATA_CONFIG,
        "output": OUTPUT_FILES,
        "logging": LOGGING_CONFIG,
        "persian": PERSIAN_CONFIG,
        "quality": QUALITY_ASSURANCE,
    }

def validate_config() -> bool:
    """
    Validate configuration settings and directory structure
    
    Returns:
        bool: True if configuration is valid
    """
    try:
        # Check if all required directories exist
        for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR]:
            if not directory.exists():
                print(f"خطا: پوشه {directory} وجود ندارد")
                return False
        
        # Check if input file path is configured
        if not DOCUMENT_CONFIG.get("input_file"):
            print("خطا: نام فایل ورودی مشخص نشده است")
            return False
        
        print("✓ تنظیمات سیستم معتبر است")
        return True
    
    except Exception as e:
        print(f"خطا در اعتبارسنجی تنظیمات: {str(e)}")
        return False

if __name__ == "__main__":
    # Test configuration
    if validate_config():
        config = get_config()
        print("تنظیمات سیستم با موفقیت بارگذاری شد")
        print(f"پوشه پروژه: {PROJECT_ROOT}")
        print(f"پوشه داده‌ها: {DATA_DIR}")
    else:
        print("خطا در تنظیمات سیستم")