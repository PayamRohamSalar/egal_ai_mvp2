# src/data_processing/document_splitter.py
"""
Document splitter for Legal Assistant
Automatically splits the complete Part2_Legals.docx file into individual laws
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import json
from docx import Document
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.config import DOCUMENT_CONFIG, OUTPUT_FILES, QUALITY_ASSURANCE
from ..utils.text_utils import PersianTextProcessor


@dataclass
class LawMetadata:
    """Metadata structure for individual laws"""
    id: str
    title: str
    approval_date: str
    approval_authority: str
    raw_content: str
    word_count: int
    extraction_timestamp: str
    quality_score: float


class DocumentSplitter:
    """
    Splits the main legal document file into individual laws
    """
    
    def __init__(self):
        self.text_processor = PersianTextProcessor()
        self.laws = []
        self.processing_stats = {
            'total_laws_found': 0,
            'valid_laws': 0,
            'invalid_laws': 0,
            'extraction_errors': 0,
            'processing_time': 0
        }
    
    def read_docx_file(self, file_path: str) -> str:
        """
        Read content from DOCX file
        
        Args:
            file_path (str): Path to the DOCX file
            
        Returns:
            str: Extracted text content
        """
        try:
            doc = Document(file_path)
            full_text = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text.strip())
            
            return '\n'.join(full_text)
        
        except Exception as e:
            raise Exception(f"خطا در خواندن فایل DOCX: {str(e)}")
    
    def identify_law_boundaries(self, text: str) -> List[Tuple[int, int]]:
        """
        Identify boundaries of individual laws in the complete text
        
        Args:
            text (str): Complete document text
            
        Returns:
            List[Tuple[int, int]]: List of (start, end) positions for each law
        """
        # Find law separators (10 or more asterisks)
        separator_pattern = DOCUMENT_CONFIG["law_separator"]
        separators = []
        
        for match in re.finditer(separator_pattern, text):
            separators.append(match.end())
        
        # Create boundaries
        boundaries = []
        start_pos = 0
        
        for separator_pos in separators:
            if start_pos < separator_pos:
                boundaries.append((start_pos, separator_pos))
            start_pos = separator_pos
        
        # Add the last section if exists
        if start_pos < len(text):
            boundaries.append((start_pos, len(text)))
        
        return boundaries
    
    def extract_law_title_and_date(self, law_text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract law title, approval date, and authority from law text
        
        Args:
            law_text (str): Individual law text
            
        Returns:
            Tuple: (title, approval_date, approval_authority)
        """
        # Clean the text first
        cleaned_text = self.text_processor.clean_text(law_text)
        
        # Look for title pattern in first few lines
        lines = cleaned_text.split('\n')[:5]
        first_content = ' '.join(lines).strip()
        
        # Pattern: Title (مصوب date)
        title_pattern = DOCUMENT_CONFIG["law_title_pattern"]
        match = re.search(title_pattern, first_content)
        
        if match:
            title = match.group(1).strip()
            date_info = match.group(2).strip()
            
            # Extract approval authority if exists in date_info
            authority = "مجلس شورای اسلامی"  # Default
            if "هیئت‌وزیران" in date_info or "هیئت وزیران" in date_info:
                authority = "هیئت‌وزیران"
            elif "شورای" in date_info:
                authority = "شورای عالی انقلاب فرهنگی"
            
            # Clean date (extract just the date part)
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2}/\d{2}|[۰-۹]{1,2}/[۰-۹]{1,2}/[۰-۹]{4}|[۰-۹]{1,2}/[۰-۹]{1,2}/[۰-۹]{2})', date_info)
            approval_date = date_match.group(1) if date_match else date_info
            
            return title, approval_date, authority
        
        # If no pattern match, try to extract from the beginning
        # Look for patterns like "قانون ..." or other legal document types
        for line in lines:
            line = line.strip()
            if any(legal_word in line for legal_word in ['قانون', 'آیین‌نامه', 'دستورالعمل']):
                # This might be the title
                return line, "نامشخص", "نامشخص"
        
        return None, None, None
    
    def calculate_quality_score(self, law_text: str, title: str) -> float:
        """
        Calculate quality score for extracted law
        
        Args:
            law_text (str): Law content
            title (str): Law title
            
        Returns:
            float: Quality score (0.0 to 1.0)
        """
        score = 0.0
        
        # Check minimum length
        if len(law_text) >= QUALITY_ASSURANCE["min_law_length"]:
            score += 0.2
        
        # Check if title exists and is meaningful
        if title and len(title) > 10:
            score += 0.2
        
        # Check for Persian content
        if self.text_processor.is_valid_persian_text(law_text):
            score += 0.2
        
        # Check for legal structure indicators
        legal_indicators = ['ماده', 'تبصره', 'بند', 'فصل']
        indicator_count = sum(1 for indicator in legal_indicators if indicator in law_text)
        if indicator_count >= 2:
            score += 0.2
        
        # Check for proper legal formatting
        if re.search(r'ماده\s*[۰-۹]+', law_text) or re.search(r'ماده\s*واحده', law_text):
            score += 0.2
        
        return min(score, 1.0)
    
    def process_individual_law(self, law_text: str, law_index: int) -> Optional[LawMetadata]:
        """
        Process individual law text and create metadata
        
        Args:
            law_text (str): Raw law text
            law_index (int): Index of the law
            
        Returns:
            Optional[LawMetadata]: Processed law metadata or None if invalid
        """
        try:
            # Clean the text
            cleaned_text = self.text_processor.clean_text(law_text)
            
            # Skip if too short or empty
            if len(cleaned_text) < QUALITY_ASSURANCE["min_law_length"]:
                return None
            
            # Extract title and metadata
            title, approval_date, approval_authority = self.extract_law_title_and_date(cleaned_text)
            
            if not title:
                # Try to create a title from content
                lines = cleaned_text.split('\n')
                for line in lines[:3]:
                    if line.strip() and len(line.strip()) > 10:
                        title = line.strip()[:100] + "..."
                        break
                
                if not title:
                    title = f"سند حقوقی شماره {law_index + 1}"
            
            # Generate unique ID
            law_id = f"law_{law_index + 1:03d}"
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(cleaned_text, title)
            
            # Create metadata object
            metadata = LawMetadata(
                id=law_id,
                title=title,
                approval_date=approval_date or "نامشخص",
                approval_authority=approval_authority or "نامشخص",
                raw_content=cleaned_text,
                word_count=len(cleaned_text.split()),
                extraction_timestamp=datetime.now().isoformat(),
                quality_score=quality_score
            )
            
            return metadata
        
        except Exception as e:
            print(f"خطا در پردازش قانون شماره {law_index + 1}: {str(e)}")
            self.processing_stats['extraction_errors'] += 1
            return None
    
    def split_document(self, input_file_path: str) -> Dict:
        """
        Main method to split the complete document into individual laws
        
        Args:
            input_file_path (str): Path to input DOCX file
            
        Returns:
            Dict: Processing results and statistics
        """
        start_time = datetime.now()
        
        try:
            print("در حال خواندن فایل اصلی...")
            full_text = self.read_docx_file(input_file_path)
            
            print("در حال تشخیص مرزهای قوانین...")
            boundaries = self.identify_law_boundaries(full_text)
            self.processing_stats['total_laws_found'] = len(boundaries)
            
            print(f"تعداد قوانین شناسایی شده: {len(boundaries)}")
            
            # Process each law
            print("در حال پردازش قوانین جداگانه...")
            valid_laws = []
            
            for i, (start, end) in enumerate(boundaries):
                law_text = full_text[start:end].strip()
                
                if law_text:
                    metadata = self.process_individual_law(law_text, i)
                    
                    if metadata and metadata.quality_score >= 0.4:  # Minimum quality threshold
                        valid_laws.append(metadata)
                        self.processing_stats['valid_laws'] += 1
                        print(f"✓ قانون {i+1}: {metadata.title[:50]}...")
                    else:
                        self.processing_stats['invalid_laws'] += 1
                        print(f"✗ قانون {i+1}: کیفیت پایین یا نامعتبر")
            
            self.laws = valid_laws
            
            # Calculate processing time
            end_time = datetime.now()
            self.processing_stats['processing_time'] = (end_time - start_time).total_seconds()
            
            # Save results
            self.save_individual_laws()
            self.save_processing_report()
            
            print(f"\n✅ پردازش کامل شد:")
            print(f"   - تعداد کل قوانین: {self.processing_stats['total_laws_found']}")
            print(f"   - قوانین معتبر: {self.processing_stats['valid_laws']}")
            print(f"   - قوانین نامعتبر: {self.processing_stats['invalid_laws']}")
            print(f"   - زمان پردازش: {self.processing_stats['processing_time']:.2f} ثانیه")
            
            return {
                'success': True,
                'stats': self.processing_stats,
                'laws': [asdict(law) for law in self.laws]
            }
        
        except Exception as e:
            error_msg = f"خطا در تفکیک اسناد: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'stats': self.processing_stats
            }
    
    def save_individual_laws(self) -> None:
        """
        Save individual laws to JSON file
        """
        try:
            laws_data = {
                'metadata': {
                    'total_laws': len(self.laws),
                    'extraction_date': datetime.now().isoformat(),
                    'source_file': 'Part2_Legals.docx'
                },
                'laws': [asdict(law) for law in self.laws]
            }
            
            output_file = OUTPUT_FILES['individual_laws']
            output_file.parent.mkdir(exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(laws_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ قوانین جداگانه در فایل ذخیره شدند: {output_file}")
        
        except Exception as e:
            print(f"خطا در ذخیره قوانین جداگانه: {str(e)}")
    
    def save_processing_report(self) -> None:
        """
        Save processing report with statistics
        """
        try:
            report = {
                'processing_summary': self.processing_stats,
                'quality_analysis': self.analyze_quality(),
                'recommendations': self.generate_recommendations(),
                'timestamp': datetime.now().isoformat()
            }
            
            output_file = OUTPUT_FILES['processing_report']
            output_file.parent.mkdir(exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"✓ گزارش پردازش ذخیره شد: {output_file}")
        
        except Exception as e:
            print(f"خطا در ذخیره گزارش: {str(e)}")
    
    def analyze_quality(self) -> Dict:
        """
        Analyze quality of extracted laws
        
        Returns:
            Dict: Quality analysis results
        """
        if not self.laws:
            return {'average_quality': 0, 'quality_distribution': {}}
        
        quality_scores = [law.quality_score for law in self.laws]
        
        quality_distribution = {
            'excellent': len([s for s in quality_scores if s >= 0.8]),
            'good': len([s for s in quality_scores if 0.6 <= s < 0.8]),
            'fair': len([s for s in quality_scores if 0.4 <= s < 0.6]),
            'poor': len([s for s in quality_scores if s < 0.4])
        }
        
        return {
            'average_quality': sum(quality_scores) / len(quality_scores),
            'quality_distribution': quality_distribution,
            'highest_quality': max(quality_scores),
            'lowest_quality': min(quality_scores)
        }
    
    def generate_recommendations(self) -> List[str]:
        """
        Generate recommendations based on processing results
        
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        
        if self.processing_stats['invalid_laws'] > self.processing_stats['valid_laws'] * 0.3:
            recommendations.append("تعداد قوانین نامعتبر بالا است. بررسی الگوریتم تشخیص توصیه می‌شود.")
        
        if self.processing_stats['extraction_errors'] > 0:
            recommendations.append(f"تعداد {self.processing_stats['extraction_errors']} خطا در استخراج وجود دارد. بررسی فرمت فایل ورودی لازم است.")
        
        quality_analysis = self.analyze_quality()
        if quality_analysis.get('average_quality', 0) < 0.6:
            recommendations.append("کیفیت متوسط استخراج پایین است. بهبود الگوریتم‌های پردازش متن پیشنهاد می‌شود.")
        
        if len(self.laws) < 10:
            recommendations.append("تعداد قوانین استخراج شده کم است. بررسی الگوریتم تفکیک لازم است.")
        
        if not recommendations:
            recommendations.append("کیفیت استخراج مطلوب است. می‌توان به مرحله بعد ادامه داد.")
        
        return recommendations
    
    def get_law_by_id(self, law_id: str) -> Optional[LawMetadata]:
        """
        Get law by ID
        
        Args:
            law_id (str): Law identifier
            
        Returns:
            Optional[LawMetadata]: Law metadata if found
        """
        for law in self.laws:
            if law.id == law_id:
                return law
        return None
    
    def get_laws_by_date_range(self, start_date: str, end_date: str) -> List[LawMetadata]:
        """
        Get laws approved within a date range
        
        Args:
            start_date (str): Start date
            end_date (str): End date
            
        Returns:
            List[LawMetadata]: List of laws in date range
        """
        # Note: This is a simplified implementation
        # In production, proper date parsing and comparison should be implemented
        matching_laws = []
        for law in self.laws:
            if start_date <= law.approval_date <= end_date:
                matching_laws.append(law)
        return matching_laws
    
    def export_summary(self) -> Dict:
        """
        Export a summary of all processed laws
        
        Returns:
            Dict: Summary information
        """
        return {
            'total_laws': len(self.laws),
            'processing_stats': self.processing_stats,
            'quality_analysis': self.analyze_quality(),
            'law_titles': [law.title for law in self.laws],
            'approval_dates': [law.approval_date for law in self.laws],
            'authorities': list(set([law.approval_authority for law in self.laws]))
        }


def split_legal_document(input_file_path: str) -> Dict:
    """
    Convenience function to split legal document
    
    Args:
        input_file_path (str): Path to input DOCX file
        
    Returns:
        Dict: Processing results
    """
    splitter = DocumentSplitter()
    return splitter.split_document(input_file_path)


# Main execution for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Test with sample file path
    input_file = Path("data/raw/Part2_Legals.docx")
    
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    
    if input_file.exists():
        print(f"شروع تفکیک فایل: {input_file}")
        result = split_legal_document(str(input_file))
        
        if result['success']:
            print("\n✅ تفکیک با موفقیت انجام شد")
            print(f"تعداد قوانین استخراج شده: {result['stats']['valid_laws']}")
        else:
            print(f"\n❌ خطا در تفکیک: {result['error']}")
    else:
        print(f"❌ فایل پیدا نشد: {input_file}")
        print("لطفاً مسیر صحیح فایل را وارد کنید.")