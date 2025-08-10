# src/data_processing/text_processor.py
"""
Text processor for Legal Assistant
Handles advanced text cleaning, standardization, and preparation for RAG
"""

import re
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime

from ..core.config import TEXT_CLEANING, PERSIAN_CONFIG
from ..utils.text_utils import PersianTextProcessor
from ..core.models import ProcessingReport, ProcessingStatus


class AdvancedTextProcessor:
    """
    Advanced text processor for legal documents
    """
    
    def __init__(self):
        self.persian_processor = PersianTextProcessor()
        self.processing_stats = {
            'documents_processed': 0,
            'text_cleaned': 0,
            'encoding_fixed': 0,
            'duplicates_removed': 0,
            'normalization_applied': 0
        }
        
        # Legal-specific cleaning patterns
        self.legal_patterns = {
            # Remove document separators
            'separators': [
                r'\*{10,}',  # Multiple asterisks
                r'={10,}',   # Multiple equals
                r'-{10,}',   # Multiple dashes
            ],
            
            # Fix common formatting issues
            'formatting_fixes': {
                r'\s*\(\s*مصوب\s*': ' (مصوب ',  # Fix approval date spacing
                r'ماده\s*(\d+)': r'ماده \1',      # Fix article numbering
                r'تبصره\s*(\d*)': r'تبصره \1',    # Fix note numbering
                r'فصل\s*(\w+)': r'فصل \1',        # Fix chapter numbering
            },
            
            # Remove artifacts
            'artifacts': [
                r'^\s*صفحه\s*\d+\s*$',           # Page numbers
                r'^\s*Page\s*\d+\s*$',           # English page numbers
                r'^\s*\d+\s*/\s*\d+\s*$',        # Page indicators
                r'^\s*\.{3,}\s*$',               # Dot lines
                r'^\s*_{3,}\s*$',                # Underscore lines
            ]
        }
    
    def clean_encoding(self, text: str) -> str:
        """
        Fix encoding issues in Persian text
        
        Args:
            text (str): Input text with potential encoding issues
            
        Returns:
            str: Text with fixed encoding
        """
        if not text:
            return ""
        
        # Common encoding fixes for Persian
        encoding_fixes = {
            'Ø§': 'ا',  # Alef
            'Ù†': 'ن',  # Noon
            'Ù…': 'م',  # Meem
            'Ø±': 'ر',  # Re
            'Ø¯': 'د',  # Dal
            'Ø³': 'س',  # Seen
            'Øª': 'ت',  # Te
            'Ù': 'ی',   # Ye
            'Ø¹': 'ع',  # Ain
            'Ù„': 'ل',  # Lam
            'Ú©': 'ک',  # Kaf
            'Ø­': 'ح',  # He
            'Ø®': 'خ',  # Khe
            'Ø¬': 'ج',  # Jeem
            'Ø²': 'ز',  # Ze
            'Ø¶': 'ض',  # Zad
            'Ø·': 'ط',  # Ta
            'Ø¸': 'ظ',  # Za
            'Ø¨': 'ب',  # Be
            'Ù¾': 'پ',  # Pe
            'Ù': 'ف',   # Fe
            'Ù‚': 'ق',  # Qaf
            'Ú¯': 'گ',  # Gaf
            'Ù‡': 'ه',  # He
            'Ø¤': 'و',  # Vav
            'Ø¦': 'ی',  # Ye with hamze
        }
        
        fixed_text = text
        for wrong, correct in encoding_fixes.items():
            fixed_text = fixed_text.replace(wrong, correct)
        
        self.processing_stats['encoding_fixed'] += 1
        return fixed_text
    
    def remove_artifacts(self, text: str) -> str:
        """
        Remove common document artifacts
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with artifacts removed
        """
        cleaned_text = text
        
        # Remove separators
        for pattern in self.legal_patterns['separators']:
            cleaned_text = re.sub(pattern, '', cleaned_text)
        
        # Remove artifacts line by line
        lines = cleaned_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check if line is an artifact
            is_artifact = False
            for pattern in self.legal_patterns['artifacts']:
                if re.match(pattern, line):
                    is_artifact = True
                    break
            
            if not is_artifact and line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def fix_formatting(self, text: str) -> str:
        """
        Fix common formatting issues in legal documents
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with fixed formatting
        """
        fixed_text = text
        
        # Apply formatting fixes
        for pattern, replacement in self.legal_patterns['formatting_fixes'].items():
            fixed_text = re.sub(pattern, replacement, fixed_text)
        
        # Fix spacing around punctuation
        fixed_text = re.sub(r'\s*([،؛؟!.])\s*', r'\1 ', fixed_text)
        fixed_text = re.sub(r'\s*([()])\s*', r' \1 ', fixed_text)
        
        # Fix multiple spaces
        fixed_text = re.sub(r'\s+', ' ', fixed_text)
        
        # Fix line breaks
        fixed_text = re.sub(r'\n\s*\n', '\n\n', fixed_text)
        
        return fixed_text.strip()
    
    def standardize_legal_terms(self, text: str) -> str:
        """
        Standardize legal terminology
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with standardized terminology
        """
        standardizations = {
            # Article references
            r'\bماده\s*(\d+)': r'ماده \1',
            r'\bماده\s*([۰-۹]+)': r'ماده \1',
            
            # Note references
            r'\bتبصره\s*(\d*)': r'تبصره \1',
            r'\bتبصره\s*([۰-۹]*)': r'تبصره \1',
            
            # Chapter references
            r'\bفصل\s*(\w+)': r'فصل \1',
            
            # Common legal phrases
            r'هیات\s*وزیران': 'هیئت‌وزیران',
            r'مجلس\s*شورای\s*اسلامی': 'مجلس شورای اسلامی',
            r'وزارت\s*علوم': 'وزارت علوم، تحقیقات و فناوری',
            
            # Date formats
            r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})': r'\1/\2/\3',
            r'([۰-۹]{1,2})\s*/\s*([۰-۹]{1,2})\s*/\s*([۰-۹]{4})': r'\1/\2/\3',
        }
        
        standardized_text = text
        for pattern, replacement in standardizations.items():
            standardized_text = re.sub(pattern, replacement, standardized_text)
        
        return standardized_text
    
    def remove_duplicates(self, text: str) -> str:
        """
        Remove duplicate sentences and paragraphs
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with duplicates removed
        """
        paragraphs = text.split('\n\n')
        unique_paragraphs = []
        seen_paragraphs = set()
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and paragraph not in seen_paragraphs:
                unique_paragraphs.append(paragraph)
                seen_paragraphs.add(paragraph)
            elif paragraph in seen_paragraphs:
                self.processing_stats['duplicates_removed'] += 1
        
        return '\n\n'.join(unique_paragraphs)
    
    def enhance_structure(self, text: str) -> str:
        """
        Enhance document structure for better parsing
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with enhanced structure
        """
        enhanced_text = text
        
        # Add clear breaks before articles
        enhanced_text = re.sub(r'(\n|^)(ماده\s+[^\s]+)', r'\1\n\2', enhanced_text)
        
        # Add clear breaks before notes
        enhanced_text = re.sub(r'(\n|^)(تبصره\s*[^\s]*)', r'\1\n\2', enhanced_text)
        
        # Add clear breaks before chapters
        enhanced_text = re.sub(r'(\n|^)(فصل\s+[^\s]+)', r'\1\n\2', enhanced_text)
        
        # Clean up extra line breaks
        enhanced_text = re.sub(r'\n{3,}', '\n\n', enhanced_text)
        
        return enhanced_text
    
    def process_text_content(self, text: str) -> str:
        """
        Process a single text content through all cleaning steps
        
        Args:
            text (str): Raw text content
            
        Returns:
            str: Processed and cleaned text
        """
        if not text:
            return ""
        
        # Step 1: Fix encoding
        cleaned_text = self.clean_encoding(text)
        
        # Step 2: Remove artifacts
        cleaned_text = self.remove_artifacts(cleaned_text)
        
        # Step 3: Fix formatting
        cleaned_text = self.fix_formatting(cleaned_text)
        
        # Step 4: Standardize legal terms
        cleaned_text = self.standardize_legal_terms(cleaned_text)
        
        # Step 5: Apply Persian normalization
        cleaned_text = self.persian_processor.normalize_persian_text(cleaned_text)
        
        # Step 6: Remove duplicates
        cleaned_text = self.remove_duplicates(cleaned_text)
        
        # Step 7: Enhance structure
        cleaned_text = self.enhance_structure(cleaned_text)
        
        # Step 8: Final cleaning
        cleaned_text = self.persian_processor.clean_text(cleaned_text)
        
        return cleaned_text
    
    def process_document_from_dict(self, law_dict: Dict) -> Dict:
        """
        Process a document from dictionary format (from individual_laws.json)
        
        Args:
            law_dict (Dict): Law dictionary from splitter output
            
        Returns:
            Dict: Processed law dictionary
        """
        try:
            # Process main content
            if 'raw_content' in law_dict and law_dict['raw_content']:
                law_dict['raw_content'] = self.process_text_content(law_dict['raw_content'])
            
            # Process title
            if 'title' in law_dict and law_dict['title']:
                law_dict['title'] = self.persian_processor.clean_text(law_dict['title'])
            
            # Update word count
            if law_dict.get('raw_content'):
                law_dict['word_count'] = len(law_dict['raw_content'].split())
            
            # Update processing timestamp
            law_dict['last_processed'] = datetime.now().isoformat()
            
            self.processing_stats['documents_processed'] += 1
            self.processing_stats['text_cleaned'] += 1
            self.processing_stats['normalization_applied'] += 1
            
            return law_dict
        
        except Exception as e:
            print(f"خطا در پردازش سند {law_dict.get('id', 'نامشخص')}: {str(e)}")
            return law_dict
    
    def process_documents_batch(self, input_file: str, output_file: str = None) -> Tuple[List[Dict], ProcessingReport]:
        """
        Process multiple documents in batch from individual_laws.json
        
        Args:
            input_file (str): Path to individual_laws.json
            output_file (str): Optional output file path
            
        Returns:
            Tuple[List[Dict], ProcessingReport]: Processed documents and report
        """
        start_time = datetime.now()
        
        try:
            # Load individual laws
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            laws = data.get('laws', [])
            
            report = ProcessingReport(
                operation_type="text_processing",
                total_items=len(laws),
                status=ProcessingStatus.PROCESSING
            )
            
            processed_laws = []
            
            print(f"در حال پردازش {len(laws)} سند...")
            
            for i, law_dict in enumerate(laws):
                try:
                    processed_law = self.process_document_from_dict(law_dict)
                    processed_laws.append(processed_law)
                    report.processed_items += 1
                    
                    print(f"✓ پردازش شد ({i+1}/{len(laws)}): {law_dict.get('title', 'نامشخص')[:50]}...")
                    
                except Exception as e:
                    error_msg = f"خطا در پردازش سند {law_dict.get('id', 'نامشخص')}: {str(e)}"
                    report.errors.append(error_msg)
                    report.failed_items += 1
                    print(f"✗ خطا ({i+1}/{len(laws)}): {error_msg}")
                    
                    # Add original document to maintain count
                    processed_laws.append(law_dict)
            
            # Update report
            report.end_time = datetime.now()
            report.status = ProcessingStatus.COMPLETED
            report.statistics = self.processing_stats.copy()
            
            # Save results if output file specified
            if output_file:
                self.save_processed_documents(processed_laws, output_file)
            
            print(f"\n✅ پردازش متن کامل شد:")
            print(f"   - موفق: {report.processed_items}")
            print(f"   - ناموفق: {report.failed_items}")
            print(f"   - زمان پردازش: {report.processing_time:.2f} ثانیه")
            
            return processed_laws, report
        
        except Exception as e:
            print(f"❌ خطا در بارگذاری یا پردازش فایل: {str(e)}")
            raise
    
    def save_processed_documents(self, processed_laws: List[Dict], output_file: str) -> None:
        """
        Save processed documents to file
        
        Args:
            processed_laws (List[Dict]): Processed law dictionaries
            output_file (str): Output file path
        """
        try:
            processed_data = {
                'metadata': {
                    'total_documents': len(processed_laws),
                    'processing_date': datetime.now().isoformat(),
                    'processing_stats': self.processing_stats
                },
                'documents': processed_laws
            }
            
            output_path = Path(output_file)
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ اسناد پردازش شده ذخیره شدند: {output_path}")
        
        except Exception as e:
            print(f"خطا در ذخیره اسناد پردازش شده: {str(e)}")
    
    def get_processing_statistics(self) -> Dict:
        """
        Get processing statistics
        
        Returns:
            Dict: Processing statistics
        """
        return self.processing_stats.copy()
    
    def export_cleaning_report(self, output_file: str) -> None:
        """
        Export cleaning report to file
        
        Args:
            output_file (str): Output file path
        """
        report = {
            'processing_statistics': self.processing_stats,
            'cleaning_patterns': self.legal_patterns,
            'timestamp': datetime.now().isoformat()
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✓ گزارش تمیزکاری ذخیره شد: {output_path}")


def process_legal_documents(input_file: str, output_file: str = None) -> Tuple[List[Dict], ProcessingReport]:
    """
    Convenience function to process legal documents from individual_laws.json
    
    Args:
        input_file (str): Path to individual_laws.json
        output_file (str): Optional output file path
        
    Returns:
        Tuple[List[Dict], ProcessingReport]: Processed documents and report
    """
    processor = AdvancedTextProcessor()
    return processor.process_documents_batch(input_file, output_file)


# Main execution for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Test text processing with sample data
    sample_text = """
قانون    مقررات انتظامی هیئت علمی  ( مصوب 22/12/1364 )
ماده1- اعضای هیئت علمی دانشگاه ها موظف به رعایت مقررات این قانون می باشند.
تبصره: این ماده شامل تمام اعضای هیات علمی می گردد.
"""
    
    processor = AdvancedTextProcessor()
    
    print("متن اصلی:")
    print(repr(sample_text))
    
    # Test individual processing steps
    print("\n1. رفع مشکلات encoding:")
    fixed_encoding = processor.clean_encoding(sample_text)
    print(repr(fixed_encoding))
    
    print("\n2. رفع مشکلات فرمت:")
    fixed_format = processor.fix_formatting(fixed_encoding)
    print(repr(fixed_format))
    
    print("\n3. استانداردسازی اصطلاحات:")
    standardized = processor.standardize_legal_terms(fixed_format)
    print(repr(standardized))
    
    print("\n4. متن نهایی:")
    final_text = processor.process_text_content(sample_text)
    print(final_text)
    
    print(f"\nآمار پردازش: {processor.get_processing_statistics()}")
    
    # Test with file if provided
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if input_file.exists():
            print(f"\nپردازش فایل: {input_file}")
            processed_docs, report = process_legal_documents(str(input_file))
            print(f"✅ {len(processed_docs)} سند پردازش شد")