# src/core/models.py
"""
Pydantic data models for Legal Assistant
Defines all data structures used throughout the system
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
from enum import Enum
import re


class DocumentType(str, Enum):
    """Legal document types"""
    LAW = "قانون"
    REGULATION = "آیین‌نامه"
    INSTRUCTION = "دستورالعمل"
    RESOLUTION = "مصوبه"
    CIRCULAR = "بخشنامه"
    UNKNOWN = "نامشخص"


class ApprovalAuthority(str, Enum):
    """Approval authorities for legal documents"""
    PARLIAMENT = "مجلس شورای اسلامی"
    CABINET = "هیئت‌وزیران"
    SUPREME_COUNCIL = "شورای عالی انقلاب فرهنگی"
    MINISTRY = "وزارتخانه"
    UNKNOWN = "نامشخص"


class SubsectionType(str, Enum):
    """Types of subsections in legal articles"""
    NUMBERED = "numbered"
    LETTERED = "lettered"
    DASH = "dash"


class ProcessingStatus(str, Enum):
    """Processing status for documents"""
    PENDING = "در انتظار"
    PROCESSING = "در حال پردازش"
    COMPLETED = "تکمیل شده"
    ERROR = "خطا"


class ChunkType(str, Enum):
    """Types of text chunks"""
    ARTICLE = "article"
    NOTE = "note"
    SUBSECTION = "subsection"
    CHAPTER_TITLE = "chapter_title"
    FOOTNOTE = "footnote"
    COMBINED = "combined"


# Base Models
class BaseEntity(BaseModel):
    """Base entity with common fields"""
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Legal Structure Models
class LegalSubsection(BaseModel):
    """Represents a subsection within an article"""
    number: str = Field(..., description="Subsection number or identifier")
    content: str = Field(..., description="Subsection content")
    type: SubsectionType = Field(..., description="Type of subsection")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('محتوای بند نمی‌تواند خالی باشد')
        return v.strip()
    
    @validator('keywords', always=True)
    def ensure_keywords_list(cls, v):
        return v if v is not None else []


class LegalNote(BaseModel):
    """Represents a note (تبصره) within an article"""
    number: str = Field(..., description="Note number or identifier")
    content: str = Field(..., description="Note content")
    subsections: List[LegalSubsection] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('محتوای تبصره نمی‌تواند خالی باشد')
        return v.strip()
    
    @validator('keywords', always=True)
    def ensure_keywords_list(cls, v):
        return v if v is not None else []
    
    @validator('subsections', always=True)
    def ensure_subsections_list(cls, v):
        return v if v is not None else []


class LegalArticle(BaseModel):
    """Represents a legal article (ماده)"""
    number: str = Field(..., description="Article number")
    title: str = Field(default="", description="Article title")
    content: str = Field(..., description="Main article content")
    subsections: List[LegalSubsection] = Field(default_factory=list)
    notes: List[LegalNote] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    word_count: Optional[int] = Field(None, description="Word count")
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('محتوای ماده نمی‌تواند خالی باشد')
        return v.strip()
    
    @validator('word_count', always=True)
    def calculate_word_count(cls, v, values):
        if 'content' in values and values['content']:
            return len(values['content'].split())
        return 0
    
    @validator('title', always=True)
    def ensure_title_string(cls, v):
        return v if v is not None else ""
    
    @validator('keywords', always=True)
    def ensure_keywords_list(cls, v):
        return v if v is not None else []
    
    @validator('subsections', always=True)
    def ensure_subsections_list(cls, v):
        return v if v is not None else []
    
    @validator('notes', always=True)
    def ensure_notes_list(cls, v):
        return v if v is not None else []


class LegalChapter(BaseModel):
    """Represents a chapter (فصل) in a legal document"""
    number: str = Field(..., description="Chapter number")
    title: str = Field(default="", description="Chapter title")
    articles: List[LegalArticle] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="Chapter summary")
    
    @validator('title', always=True)
    def ensure_title_string(cls, v):
        return v if v is not None else ""
    
    @validator('articles', always=True)
    def ensure_articles_list(cls, v):
        return v if v is not None else []
    
    @property
    def article_count(self) -> int:
        """Get number of articles in chapter"""
        return len(self.articles)
    
    @property
    def total_word_count(self) -> int:
        """Get total word count for all articles in chapter"""
        return sum(article.word_count or 0 for article in self.articles)


# Document Models
class DocumentMetadata(BaseModel):
    """Metadata for legal documents"""
    word_count: int = Field(0, description="Total word count")
    character_count: int = Field(0, description="Total character count")
    structure_type: str = Field("نامشخص", description="Document structure type")
    has_footnotes: bool = Field(False, description="Whether document has footnotes")
    complexity_score: float = Field(0.0, ge=0.0, le=1.0, description="Document complexity score")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Document quality score")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    extraction_errors: List[str] = Field(default_factory=list, description="Extraction errors")
    
    @validator('extraction_errors', always=True)
    def ensure_errors_list(cls, v):
        return v if v is not None else []


class LegalDocument(BaseEntity):
    """Complete legal document model"""
    title: str = Field(..., description="Document title")
    approval_date: str = Field(..., description="Approval date")
    approval_authority: str = Field(..., description="Approval authority")
    document_type: str = Field(..., description="Document type")
    chapters: List[LegalChapter] = Field(default_factory=list)
    standalone_articles: List[LegalArticle] = Field(default_factory=list)
    footnotes: List[str] = Field(default_factory=list)
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    raw_content: Optional[str] = Field(None, description="Original raw content")
    status: ProcessingStatus = Field(ProcessingStatus.PENDING)
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('عنوان سند نمی‌تواند خالی باشد')
        return v.strip()
    
    @validator('approval_date')
    def approval_date_not_empty(cls, v):
        if not v or not v.strip():
            return "نامشخص"
        return v.strip()
    
    @validator('approval_authority')
    def approval_authority_not_empty(cls, v):
        if not v or not v.strip():
            return "نامشخص"
        return v.strip()
    
    @validator('document_type')
    def document_type_not_empty(cls, v):
        if not v or not v.strip():
            return "نامشخص"
        return v.strip()
    
    @validator('chapters', always=True)
    def ensure_chapters_list(cls, v):
        return v if v is not None else []
    
    @validator('standalone_articles', always=True)
    def ensure_standalone_articles_list(cls, v):
        return v if v is not None else []
    
    @validator('footnotes', always=True)
    def ensure_footnotes_list(cls, v):
        return v if v is not None else []
    
    @property
    def total_articles(self) -> int:
        """Get total number of articles"""
        chapter_articles = sum(len(chapter.articles) for chapter in self.chapters)
        return chapter_articles + len(self.standalone_articles)
    
    @property
    def total_word_count(self) -> int:
        """Get total word count for entire document"""
        chapter_words = sum(chapter.total_word_count for chapter in self.chapters)
        standalone_words = sum(article.word_count or 0 for article in self.standalone_articles)
        return chapter_words + standalone_words


# Chunking Models
class TextChunk(BaseModel):
    """Represents a chunk of text for RAG"""
    id: str = Field(..., description="Chunk identifier")
    document_id: str = Field(..., description="Source document ID")
    content: str = Field(..., description="Chunk content")
    chunk_type: ChunkType = Field(..., description="Type of chunk")
    position: int = Field(..., description="Position in document")
    word_count: int = Field(0, description="Word count")
    character_count: int = Field(0, description="Character count")
    keywords: List[str] = Field(default_factory=list)
    legal_references: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('محتوای chunk نمی‌تواند خالی باشد')
        return v.strip()
    
    @validator('word_count', always=True)
    def calculate_word_count(cls, v, values):
        if 'content' in values and values['content']:
            return len(values['content'].split())
        return 0
    
    @validator('character_count', always=True)
    def calculate_character_count(cls, v, values):
        if 'content' in values and values['content']:
            return len(values['content'])
        return 0
    
    @validator('keywords', always=True)
    def ensure_keywords_list(cls, v):
        return v if v is not None else []
    
    @validator('legal_references', always=True)
    def ensure_legal_references_list(cls, v):
        return v if v is not None else []
    
    @validator('metadata', always=True)
    def ensure_metadata_dict(cls, v):
        return v if v is not None else {}


# Processing Models
class ProcessingReport(BaseModel):
    """Report for document processing operations"""
    operation_type: str = Field(..., description="Type of operation")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: ProcessingStatus = Field(ProcessingStatus.PENDING)
    total_items: int = Field(0, description="Total items to process")
    processed_items: int = Field(0, description="Successfully processed items")
    failed_items: int = Field(0, description="Failed items")
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('errors', always=True)
    def ensure_errors_list(cls, v):
        return v if v is not None else []
    
    @validator('warnings', always=True)
    def ensure_warnings_list(cls, v):
        return v if v is not None else []
    
    @validator('statistics', always=True)
    def ensure_statistics_dict(cls, v):
        return v if v is not None else {}
    
    @property
    def processing_time(self) -> Optional[float]:
        """Calculate processing time in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100.0


class QualityAssessment(BaseModel):
    """Quality assessment for processed documents"""
    document_id: str = Field(..., description="Document ID")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    structure_score: float = Field(..., ge=0.0, le=1.0, description="Structure quality")
    content_score: float = Field(..., ge=0.0, le=1.0, description="Content quality")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness score")
    issues: List[str] = Field(default_factory=list, description="Quality issues found")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    assessment_date: datetime = Field(default_factory=datetime.now)
    
    @validator('issues', always=True)
    def ensure_issues_list(cls, v):
        return v if v is not None else []
    
    @validator('recommendations', always=True)
    def ensure_recommendations_list(cls, v):
        return v if v is not None else []


# Search and Retrieval Models
class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., description="Search query text")
    document_types: List[str] = Field(default_factory=list)
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")
    authorities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    
    @validator('query')
    def query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('متن جستجو نمی‌تواند خالی باشد')
        return v.strip()
    
    @validator('document_types', always=True)
    def ensure_document_types_list(cls, v):
        return v if v is not None else []
    
    @validator('authorities', always=True)
    def ensure_authorities_list(cls, v):
        return v if v is not None else []
    
    @validator('keywords', always=True)
    def ensure_keywords_list(cls, v):
        return v if v is not None else []


class SearchResult(BaseModel):
    """Search result model"""
    document_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    snippet: str = Field(..., description="Text snippet")
    highlights: List[str] = Field(default_factory=list, description="Highlighted terms")
    chunk_id: Optional[str] = Field(None, description="Source chunk ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('highlights', always=True)
    def ensure_highlights_list(cls, v):
        return v if v is not None else []
    
    @validator('metadata', always=True)
    def ensure_metadata_dict(cls, v):
        return v if v is not None else {}


# Configuration Models
class ProcessingConfig(BaseModel):
    """Configuration for document processing"""
    min_chunk_size: int = Field(200, ge=50, description="Minimum chunk size")
    max_chunk_size: int = Field(1000, ge=100, description="Maximum chunk size")
    chunk_overlap: int = Field(100, ge=0, description="Overlap between chunks")
    extract_keywords: bool = Field(True, description="Whether to extract keywords")
    max_keywords: int = Field(20, ge=1, description="Maximum keywords per item")
    quality_threshold: float = Field(0.4, ge=0.0, le=1.0, description="Minimum quality threshold")
    
    @validator('chunk_overlap')
    def overlap_less_than_max_size(cls, v, values):
        if 'max_chunk_size' in values and v >= values['max_chunk_size']:
            raise ValueError('Overlap باید کمتر از حداکثر اندازه chunk باشد')
        return v


# Embedding and RAG Models
class EmbeddingModel(BaseModel):
    """Embedding model configuration"""
    model_name: str = Field(..., description="Name of the embedding model")
    dimension: int = Field(..., description="Embedding dimension")
    max_sequence_length: int = Field(512, description="Maximum sequence length")
    language: str = Field("fa", description="Language code")
    device: str = Field("cpu", description="Device to run on")


class VectorStoreConfig(BaseModel):
    """Vector store configuration"""
    store_type: str = Field("faiss", description="Type of vector store")
    index_path: str = Field(..., description="Path to store index")
    embedding_dim: int = Field(..., description="Embedding dimension")
    similarity_metric: str = Field("cosine", description="Similarity metric")
    nlist: int = Field(100, description="Number of clusters for FAISS")


class RAGConfig(BaseModel):
    """RAG system configuration"""
    embedding_model: EmbeddingModel = Field(..., description="Embedding model config")
    vector_store: VectorStoreConfig = Field(..., description="Vector store config")
    retrieval_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    rerank: bool = Field(True, description="Whether to re-rank results")


# Utility functions for model validation and creation
def validate_persian_date(date_str: str) -> bool:
    """Validate Persian date format"""
    if not date_str or date_str.strip() == "نامشخص":
        return True
    
    patterns = [
        r'^\d{1,2}/\d{1,2}/\d{4}$',
        r'^\d{1,2}/\d{1,2}/\d{2}$',
        r'^[۰-۹]{1,2}/[۰-۹]{1,2}/[۰-۹]{4}$',
        r'^[۰-۹]{1,2}/[۰-۹]{1,2}/[۰-۹]{2}$'
    ]
    return any(re.match(pattern, date_str.strip()) for pattern in patterns)


def create_chunk_id(document_id: str, chunk_index: int) -> str:
    """Create standardized chunk ID"""
    return f"{document_id}_chunk_{chunk_index:04d}"


def create_document_id(title: str, approval_date: str) -> str:
    """Create standardized document ID"""
    # Clean title for ID creation
    clean_title = re.sub(r'[^\w\s]', '', title)[:50]
    clean_title = re.sub(r'\s+', '_', clean_title)
    
    # Clean date
    clean_date = re.sub(r'[^\d]', '', approval_date) if approval_date != "نامشخص" else "unknown"
    
    return f"doc_{clean_title}_{clean_date}"


def map_approval_authority(authority_text: str) -> str:
    """Map authority text to standardized value"""
    authority_text = authority_text.lower().strip()
    
    if any(term in authority_text for term in ['مجلس', 'پارلمان']):
        return ApprovalAuthority.PARLIAMENT.value
    elif any(term in authority_text for term in ['هیئت', 'هیات', 'کابینه']):
        return ApprovalAuthority.CABINET.value
    elif 'شورای' in authority_text and 'عالی' in authority_text:
        return ApprovalAuthority.SUPREME_COUNCIL.value
    elif 'وزارت' in authority_text or 'وزیر' in authority_text:
        return ApprovalAuthority.MINISTRY.value
    else:
        return ApprovalAuthority.UNKNOWN.value


def map_document_type(title: str) -> str:
    """Map document title to document type"""
    title_lower = title.lower()
    
    if 'قانون' in title_lower:
        return DocumentType.LAW.value
    elif 'آیین‌نامه' in title_lower or 'آیین نامه' in title_lower:
        return DocumentType.REGULATION.value
    elif 'دستورالعمل' in title_lower:
        return DocumentType.INSTRUCTION.value
    elif 'مصوبه' in title_lower:
        return DocumentType.RESOLUTION.value
    elif 'بخشنامه' in title_lower:
        return DocumentType.CIRCULAR.value
    else:
        return DocumentType.UNKNOWN.value


# Export all models for easy imports
__all__ = [
    # Enums
    'DocumentType', 'ApprovalAuthority', 'SubsectionType', 'ProcessingStatus', 'ChunkType',
    
    # Base Models
    'BaseEntity',
    
    # Legal Structure Models
    'LegalSubsection', 'LegalNote', 'LegalArticle', 'LegalChapter',
    
    # Document Models
    'DocumentMetadata', 'LegalDocument',
    
    # Chunking Models
    'TextChunk',
    
    # Processing Models
    'ProcessingReport', 'QualityAssessment',
    
    # Search Models
    'SearchQuery', 'SearchResult',
    
    # Configuration Models
    'ProcessingConfig', 'EmbeddingModel', 'VectorStoreConfig', 'RAGConfig',
    
    # Utility Functions
    'validate_persian_date', 'create_chunk_id', 'create_document_id',
    'map_approval_authority', 'map_document_type'
]


# Example usage and testing
if __name__ == "__main__":
    # Test model creation
    try:
        # Create a sample legal article
        article = LegalArticle(
            number="ماده ۱",
            title="تعاریف",
            content="در این قانون کلمات و عبارات زیر در معانی مشروح مقابل آنها به کار می‌روند."
        )
        
        print("✓ مدل ماده حقوقی با موفقیت ایجاد شد")
        print(f"   شماره: {article.number}")
        print(f"   تعداد کلمات: {article.word_count}")
        
        # Create a sample document
        doc = LegalDocument(
            id="doc_001",
            title="قانون نمونه",
            approval_date="01/01/1400",
            approval_authority="مجلس شورای اسلامی",
            document_type="قانون",
            standalone_articles=[article]
        )
        
        print("✓ مدل سند حقوقی با موفقیت ایجاد شد")
        print(f"   عنوان: {doc.title}")
        print(f"   تعداد مواد: {doc.total_articles}")
        
        # Test JSON serialization
        json_data = doc.json(ensure_ascii=False, indent=2)
        print("✓ سریالایزیشن JSON موفقیت‌آمیز بود")
        
        # Test utility functions
        print(f"✓ اعتبارسنجی تاریخ: {validate_persian_date('01/01/1400')}")
        print(f"✓ ID ایجاد شده: {create_document_id('قانون نمونه', '01/01/1400')}")
        
    except Exception as e:
        print(f"❌ خطا در تست مدل‌ها: {str(e)}")
        import traceback
        traceback.print_exc()