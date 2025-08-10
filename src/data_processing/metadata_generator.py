# src/data_processing/metadata_generator.py
"""
Metadata generator for Legal Assistant
Generates comprehensive metadata for legal documents and their components
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import Counter
import json
from pathlib import Path

from ..core.models import (
    LegalDocument, DocumentMetadata, QualityAssessment,
    TextChunk, ProcessingReport, ProcessingStatus
)
from ..utils.text_utils import PersianTextProcessor
from ..core.config import METADATA_CONFIG, PERSIAN_CONFIG


class MetadataGenerator:
    """
    Generates metadata for legal documents and text chunks
    """
    
    def __init__(self):
        self.text_processor = PersianTextProcessor()
        self.generation_stats = {
            'documents_processed': 0,
            'keywords_extracted': 0,
            'dates_extracted': 0,
            'references_found': 0,
            'quality_assessments': 0
        }
        
        # Legal authority patterns
        self.authority_patterns = {
            'مجلس شورای اسلامی': [
                r'مجلس\s*شورای\s*اسلامی',
                r'مجلس',
                r'پارلمان'
            ],
            'هیئت‌وزیران': [
                r'هیئت\s*وزیران',
                r'هیات\s*وزیران',
                r'کابینه'
            ],
            'شورای عالی انقلاب فرهنگی': [
                r'شورای\s*عالی\s*انقلاب\s*فرهنگی',
                r'شعاف'
            ],
            'وزارت علوم': [
                r'وزارت\s*علوم',
                r'وزیر\s*علوم'
            ]
        }
        
        # Common legal keywords for categorization
        self.legal_categories = {
            'اداری': ['اداری', 'ادارات', 'بروکراسی', 'مدیریت', 'سازمان'],
            'آموزشی': ['آموزش', 'تحصیل', 'دانشگاه', 'دانشکده', 'دانشجو'],
            'پژوهشی': ['پژوهش', 'تحقیق', 'تحقیقات', 'علمی', 'فناوری'],
            'مالی': ['مالی', 'بودجه', 'هزینه', 'اعتبار', 'تأمین'],
            'حقوقی': ['حقوق', 'قانون', 'مقررات', 'آیین‌نامه', 'دستورالعمل'],
            'انتظامی': ['انتظامی', 'تأدیب', 'تخلف', 'جزا', 'مجازات']
        }
    
    def extract_document_keywords(self, document: LegalDocument) -> List[str]:
        """
        Extract comprehensive keywords from document
        
        Args:
            document (LegalDocument): Document to analyze
            
        Returns:
            List[str]: Extracted keywords
        """
        all_text = []
        
        # Collect all text content
        all_text.append(document.title)
        
        # Chapter content
        for chapter in document.chapters:
            all_text.append(chapter.title)
            for article in chapter.articles:
                all_text.extend([article.title, article.content])
                for subsection in article.subsections:
                    all_text.append(subsection.content)
                for note in article.notes:
                    all_text.append(note.content)
        
        # Standalone articles
        for article in document.standalone_articles:
            all_text.extend([article.title, article.content])
            for subsection in article.subsections:
                all_text.append(subsection.content)
            for note in article.notes:
                all_text.append(note.content)
        
        # Footnotes
        all_text.extend(document.footnotes)
        
        # Extract keywords from combined text
        combined_text = ' '.join(filter(None, all_text))
        keywords = self.text_processor.extract_keywords(
            combined_text, 
            max_keywords=METADATA_CONFIG.get('max_keywords_per_document', 20)
        )
        
        self.generation_stats['keywords_extracted'] += len(keywords)
        return keywords
    
    def extract_legal_references(self, text: str) -> List[Dict[str, str]]:
        """
        Extract legal references from text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            List[Dict]: Legal references with type and text
        """
        references = []
        
        # Reference patterns
        patterns = [
            (r'قانون\s+([^.،؛\n]+)', 'law'),
            (r'آیین‌نامه\s+([^.،؛\n]+)', 'regulation'),
            (r'دستورالعمل\s+([^.،؛\n]+)', 'instruction'),
            (r'ماده\s*([۰-۹]+|واحده)', 'article'),
            (r'تبصره\s*([۰-۹]*)', 'note'),
            (r'بند\s*([۰-۹]+)', 'subsection'),
            (r'فصل\s*([۰-۹]+)', 'chapter'),
            (r'مصوب\s*([۰-۹/]+)', 'approval_date'),
        ]
        
        for pattern, ref_type in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                references.append({
                    'type': ref_type,
                    'text': match.group(0),
                    'value': match.group(1) if match.groups() else match.group(0),
                    'position': match.start()
                })
        
        self.generation_stats['references_found'] += len(references)
        return references
    
    def identify_approval_authority(self, text: str) -> str:
        """
        Identify the approval authority from document text
        
        Args:
            text (str): Document text
            
        Returns:
            str: Identified authority
        """
        text_lower = text.lower()
        
        for authority, patterns in self.authority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return authority
        
        return 'نامشخص'
    
    def categorize_document(self, document: LegalDocument) -> List[str]:
        """
        Categorize document based on content
        
        Args:
            document (LegalDocument): Document to categorize
            
        Returns:
            List[str]: Document categories
        """
        # Combine all text for analysis
        all_text = document.title.lower()
        
        if document.raw_content:
            all_text += " " + document.raw_content.lower()
        
        categories = []
        
        for category, keywords in self.legal_categories.items():
            matches = sum(1 for keyword in keywords if keyword in all_text)
            if matches >= 2:  # At least 2 keyword matches
                categories.append(category)
        
        # Default category if none found
        if not categories:
            if document.document_type.value == 'قانون':
                categories.append('قانونی')
            else:
                categories.append('عمومی')
        
        return categories
    
    def calculate_complexity_metrics(self, document: LegalDocument) -> Dict[str, float]:
        """
        Calculate document complexity metrics
        
        Args:
            document (LegalDocument): Document to analyze
            
        Returns:
            Dict[str, float]: Complexity metrics
        """
        metrics = {
            'structural_complexity': 0.0,
            'textual_complexity': 0.0,
            'legal_complexity': 0.0,
            'overall_complexity': 0.0
        }
        
        # Structural complexity
        chapter_count = len(document.chapters)
        total_articles = document.total_articles
        total_subsections = sum(
            len(article.subsections) 
            for chapter in document.chapters 
            for article in chapter.articles
        ) + sum(
            len(article.subsections) 
            for article in document.standalone_articles
        )
        total_notes = sum(
            len(article.notes) 
            for chapter in document.chapters 
            for article in chapter.articles
        ) + sum(
            len(article.notes) 
            for article in document.standalone_articles
        )
        
        # Normalize structural complexity (0-1 scale)
        metrics['structural_complexity'] = min(
            (chapter_count * 0.1 + total_articles * 0.05 + 
             total_subsections * 0.02 + total_notes * 0.03), 1.0
        )
        
        # Textual complexity
        total_words = document.total_word_count
        avg_sentence_length = 0
        
        if document.raw_content:
            sentences = self.text_processor.split_sentences(document.raw_content)
            if sentences:
                avg_sentence_length = total_words / len(sentences)
        
        # Normalize textual complexity
        metrics['textual_complexity'] = min(
            (total_words / 10000 + avg_sentence_length / 50), 1.0
        )
        
        # Legal complexity (based on legal references and terminology)
        legal_refs = self.extract_legal_references(document.raw_content or "")
        legal_terms_count = len([
            term for term in PERSIAN_CONFIG['common_legal_terms']
            if term in (document.raw_content or "").lower()
        ])
        
        metrics['legal_complexity'] = min(
            (len(legal_refs) * 0.05 + legal_terms_count * 0.02), 1.0
        )
        
        # Overall complexity (weighted average)
        metrics['overall_complexity'] = (
            metrics['structural_complexity'] * 0.4 +
            metrics['textual_complexity'] * 0.3 +
            metrics['legal_complexity'] * 0.3
        )
        
        return metrics
    
    def assess_document_quality(self, document: LegalDocument) -> QualityAssessment:
        """
        Assess document quality
        
        Args:
            document (LegalDocument): Document to assess
            
        Returns:
            QualityAssessment: Quality assessment results
        """
        issues = []
        recommendations = []
        
        # Structure quality
        structure_score = 1.0
        
        if not document.title.strip():
            issues.append("عنوان سند خالی است")
            structure_score -= 0.3
        
        if document.total_articles == 0:
            issues.append("هیچ ماده‌ای در سند یافت نشد")
            structure_score -= 0.5
        
        if not document.approval_date or document.approval_date == "نامشخص":
            issues.append("تاریخ تصویب مشخص نیست")
            structure_score -= 0.2
        
        # Content quality
        content_score = 1.0
        
        if document.total_word_count < 50:
            issues.append("محتوای سند بسیار کوتاه است")
            content_score -= 0.4
        
        # Check for Persian content
        if document.raw_content and not self.text_processor.is_valid_persian_text(document.raw_content):
            issues.append("محتوای فارسی نامعتبر یا ناکافی")
            content_score -= 0.3
        
        # Completeness score
        completeness_score = 1.0
        
        required_fields = [document.title, document.approval_date, document.document_type]
        missing_fields = sum(1 for field in required_fields if not field or str(field) == "نامشخص")
        completeness_score -= missing_fields * 0.2
        
        # Overall score
        overall_score = (structure_score + content_score + completeness_score) / 3
        
        # Generate recommendations
        if overall_score < 0.6:
            recommendations.append("کیفیت کلی سند پایین است - بازنگری کامل توصیه می‌شود")
        
        if structure_score < 0.7:
            recommendations.append("ساختار سند نیاز به بهبود دارد")
        
        if content_score < 0.7:
            recommendations.append("محتوای سند نیاز به تکمیل و بهبود دارد")
        
        if not recommendations:
            recommendations.append("کیفیت سند قابل قبول است")
        
        assessment = QualityAssessment(
            document_id=document.id,
            overall_score=max(0.0, min(1.0, overall_score)),
            structure_score=max(0.0, min(1.0, structure_score)),
            content_score=max(0.0, min(1.0, content_score)),
            completeness_score=max(0.0, min(1.0, completeness_score)),
            issues=issues,
            recommendations=recommendations
        )
        
        self.generation_stats['quality_assessments'] += 1
        return assessment
    
    def generate_document_metadata(self, document: LegalDocument) -> DocumentMetadata:
        """
        Generate comprehensive metadata for a document
        
        Args:
            document (LegalDocument): Document to analyze
            
        Returns:
            DocumentMetadata: Generated metadata
        """
        # Extract all information
        keywords = self.extract_document_keywords(document)
        legal_refs = self.extract_legal_references(document.raw_content or "")
        categories = self.categorize_document(document)
        complexity_metrics = self.calculate_complexity_metrics(document)
        
        # Create comprehensive metadata
        metadata = DocumentMetadata(
            word_count=document.total_word_count,
            character_count=len(document.raw_content or ""),
            structure_type="با فصل" if document.chapters else "بدون فصل",
            has_footnotes=len(document.footnotes) > 0,
            complexity_score=complexity_metrics['overall_complexity'],
            quality_score=document.metadata.quality_score if hasattr(document.metadata, 'quality_score') else 0.0
        )
        
        # Add extended metadata
        extended_metadata = {
            'keywords': keywords,
            'categories': categories,
            'legal_references': legal_refs,
            'complexity_metrics': complexity_metrics,
            'statistics': {
                'chapter_count': len(document.chapters),
                'article_count': document.total_articles,
                'footnote_count': len(document.footnotes),
                'approval_authority': document.approval_authority.value
            },
            'generation_timestamp': datetime.now().isoformat()
        }
        
        # Store extended metadata in the extraction_errors field (repurposing for metadata)
        metadata.extraction_errors = [json.dumps(extended_metadata, ensure_ascii=False)]
        
        self.generation_stats['documents_processed'] += 1
        return metadata
    
    def generate_chunk_metadata(self, chunk: TextChunk, document: LegalDocument) -> Dict:
        """
        Generate metadata for a text chunk
        
        Args:
            chunk (TextChunk): Chunk to analyze
            document (LegalDocument): Source document
            
        Returns:
            Dict: Enhanced chunk metadata
        """
        # Extract chunk-specific information
        chunk_keywords = self.text_processor.extract_keywords(chunk.content, max_keywords=10)
        chunk_refs = self.extract_legal_references(chunk.content)
        
        # Calculate chunk importance score
        importance_score = 0.0
        
        # Higher score for main articles
        if chunk.chunk_type == 'article':
            importance_score += 0.5
        elif chunk.chunk_type == 'note':
            importance_score += 0.3
        elif chunk.chunk_type == 'subsection':
            importance_score += 0.2
        
        # Higher score for chunks with more legal references
        importance_score += min(len(chunk_refs) * 0.1, 0.3)
        
        # Higher score for chunks with legal keywords
        legal_keyword_count = sum(
            1 for keyword in chunk_keywords 
            if keyword in PERSIAN_CONFIG['common_legal_terms']
        )
        importance_score += min(legal_keyword_count * 0.05, 0.2)
        
        enhanced_metadata = {
            'chunk_keywords': chunk_keywords,
            'legal_references': chunk_refs,
            'importance_score': min(importance_score, 1.0),
            'source_document_title': document.title,
            'source_document_type': document.document_type.value,
            'extraction_quality': self.assess_chunk_quality(chunk),
            'generation_timestamp': datetime.now().isoformat()
        }
        
        return enhanced_metadata
    
    def assess_chunk_quality(self, chunk: TextChunk) -> float:
        """
        Assess the quality of a text chunk
        
        Args:
            chunk (TextChunk): Chunk to assess
            
        Returns:
            float: Quality score (0.0 to 1.0)
        """
        score = 1.0
        
        # Length assessment
        if chunk.character_count < 100:
            score -= 0.3
        elif chunk.character_count > 1500:
            score -= 0.2
        
        # Content validity
        if not self.text_processor.is_valid_persian_text(chunk.content):
            score -= 0.4
        
        # Structure assessment
        if chunk.chunk_type in ['article', 'note'] and len(chunk.content.split()) < 10:
            score -= 0.2
        
        return max(0.0, score)
    
    def generate_processing_summary(self, documents: List[LegalDocument], 
                                  chunks: List[TextChunk]) -> Dict:
        """
        Generate comprehensive processing summary
        
        Args:
            documents (List[LegalDocument]): Processed documents
            chunks (List[TextChunk]): Generated chunks
            
        Returns:
            Dict: Processing summary
        """
        # Document statistics
        doc_stats = {
            'total_documents': len(documents),
            'document_types': Counter(doc.document_type.value for doc in documents),
            'approval_authorities': Counter(doc.approval_authority.value for doc in documents),
            'total_articles': sum(doc.total_articles for doc in documents),
            'total_chapters': sum(len(doc.chapters) for doc in documents),
            'average_word_count': sum(doc.total_word_count for doc in documents) / len(documents) if documents else 0
        }
        
        # Chunk statistics
        chunk_stats = {
            'total_chunks': len(chunks),
            'chunk_types': Counter(chunk.chunk_type for chunk in chunks),
            'average_chunk_size': sum(chunk.character_count for chunk in chunks) / len(chunks) if chunks else 0,
            'size_distribution': {
                'small': len([c for c in chunks if c.character_count < 300]),
                'medium': len([c for c in chunks if 300 <= c.character_count <= 800]),
                'large': len([c for c in chunks if c.character_count > 800])
            }
        }
        
        # Quality overview
        quality_assessments = [self.assess_document_quality(doc) for doc in documents]
        quality_stats = {
            'average_quality': sum(qa.overall_score for qa in quality_assessments) / len(quality_assessments) if quality_assessments else 0,
            'high_quality_documents': len([qa for qa in quality_assessments if qa.overall_score >= 0.8]),
            'problematic_documents': len([qa for qa in quality_assessments if qa.overall_score < 0.6]),
            'common_issues': Counter([issue for qa in quality_assessments for issue in qa.issues])
        }
        
        return {
            'generation_timestamp': datetime.now().isoformat(),
            'generation_statistics': self.generation_stats,
            'document_statistics': doc_stats,
            'chunk_statistics': chunk_stats,
            'quality_statistics': quality_stats,
            'recommendations': self.generate_system_recommendations(documents, chunks)
        }
    
    def generate_system_recommendations(self, documents: List[LegalDocument], 
                                     chunks: List[TextChunk]) -> List[str]:
        """
        Generate system-level recommendations
        
        Args:
            documents (List[LegalDocument]): Processed documents
            chunks (List[TextChunk]): Generated chunks
            
        Returns:
            List[str]: System recommendations
        """
        recommendations = []
        
        if not documents:
            recommendations.append("هیچ سندی پردازش نشده است")
            return recommendations
        
        # Document quality recommendations
        avg_quality = sum(self.assess_document_quality(doc).overall_score for doc in documents) / len(documents)
        
        if avg_quality < 0.6:
            recommendations.append("کیفیت متوسط اسناد پایین است - بازنگری فرآیند استخراج لازم")
        
        # Chunk size recommendations
        if chunks:
            avg_chunk_size = sum(chunk.character_count for chunk in chunks) / len(chunks)
            
            if avg_chunk_size < 200:
                recommendations.append("اندازه متوسط chunks کوچک است - افزایش حداقل اندازه توصیه می‌شود")
            elif avg_chunk_size > 1200:
                recommendations.append("اندازه متوسط chunks بزرگ است - کاهش حداکثر اندازه توصیه می‌شود")
        
        # Structure recommendations
        documents_with_chapters = len([doc for doc in documents if doc.chapters])
        if documents_with_chapters < len(documents) * 0.5:
            recommendations.append("اکثر اسناد ساختار فصل‌بندی ندارند - بررسی الگوریتم تشخیص فصل")
        
        if not recommendations:
            recommendations.append("پردازش با کیفیت مطلوبی انجام شده است")
        
        return recommendations
    
    def export_metadata_report(self, documents: List[LegalDocument], 
                             chunks: List[TextChunk], output_file: str) -> None:
        """
        Export comprehensive metadata report
        
        Args:
            documents (List[LegalDocument]): Processed documents
            chunks (List[TextChunk]): Generated chunks
            output_file (str): Output file path
        """
        # Generate comprehensive report
        report = {
            'metadata_report': {
                'summary': self.generate_processing_summary(documents, chunks),
                'document_assessments': [
                    {
                        'document_id': doc.id,
                        'title': doc.title,
                        'quality_assessment': self.assess_document_quality(doc).dict(),
                        'metadata': self.generate_document_metadata(doc).dict()
                    }
                    for doc in documents
                ],
                'generation_statistics': self.generation_stats
            }
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✓ گزارش جامع metadata ذخیره شد: {output_path}")


def generate_comprehensive_metadata(documents: List[LegalDocument], 
                                  chunks: List[TextChunk]) -> Dict:
    """
    Generate comprehensive metadata for documents and chunks
    
    Args:
        documents (List[LegalDocument]): Documents to analyze
        chunks (List[TextChunk]): Chunks to analyze
        
    Returns:
        Dict: Comprehensive metadata
    """
    generator = MetadataGenerator()
    return generator.generate_processing_summary(documents, chunks)


# Main execution for testing
if __name__ == "__main__":
    # Test metadata generation
    from ..core.models import LegalDocument, LegalArticle, DocumentType, ApprovalAuthority
    
    # Create sample document
    sample_article = LegalArticle(
        number="ماده ۱",
        title="تعاریف",
        content="در این قانون منظور از دانشگاه، مؤسسه آموزش عالی است که دارای مجوز رسمی می‌باشد."
    )
    
    sample_document = LegalDocument(
        id="test_doc_001",
        title="قانون آموزش عالی",
        approval_date="01/01/1400",
        approval_authority=ApprovalAuthority.PARLIAMENT,
        document_type=DocumentType.LAW,
        standalone_articles=[sample_article],
        raw_content="قانون آموزش عالی (مصوب 01/01/1400) ماده ۱ - در این قانون منظور از دانشگاه..."
    )
    
    # Test metadata generation
    generator = MetadataGenerator()
    
    print("شروع تست تولید metadata...")
    
    # Test document metadata
    doc_metadata = generator.generate_document_metadata(sample_document)
    print(f"✓ Metadata سند: complexity={doc_metadata.complexity_score:.2f}")
    
    # Test quality assessment
    quality = generator.assess_document_quality(sample_document)
    print(f"✓ ارزیابی کیفیت: overall={quality.overall_score:.2f}")
    
    # Test processing summary
    summary = generator.generate_processing_summary([sample_document], [])
    print(f"✓ خلاصه پردازش: {summary['document_statistics']['total_documents']} سند")
    
    print(f"\nآمار تولید metadata: {generator.generation_stats}")