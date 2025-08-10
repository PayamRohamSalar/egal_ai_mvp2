# ===============================================
# src/__init__.py
# ===============================================
"""
Legal Assistant - Main package
AI-powered legal document processing and retrieval system
"""

__version__ = "1.0.0"
__author__ = "Legal Assistant Team"
__description__ = "دستیار حقوقی هوشمند برای پردازش اسناد حقوقی"

# Core imports
from src.core.config import get_config, validate_config
from src.core.models import LegalDocument, TextChunk, ProcessingReport

__all__ = [
    'get_config', 'validate_config',
    'LegalDocument', 'TextChunk', 'ProcessingReport'
]

# ===============================================
# src/core/__init__.py
# ===============================================
"""
Core modules for Legal Assistant
Contains configuration, models, and base utilities
"""

from .config import get_config, validate_config, OUTPUT_FILES, PROJECT_ROOT
from .models import (
    # Enums
    DocumentType, ApprovalAuthority, SubsectionType, ProcessingStatus, ChunkType,
    
    # Base Models
    BaseEntity,
    
    # Legal Structure Models
    LegalSubsection, LegalNote, LegalArticle, LegalChapter,
    
    # Document Models
    DocumentMetadata, LegalDocument,
    
    # Chunking Models
    TextChunk,
    
    # Processing Models
    ProcessingReport, QualityAssessment,
    
    # Search Models
    SearchQuery, SearchResult,
    
    # Configuration Models
    ProcessingConfig, EmbeddingModel, VectorStoreConfig, RAGConfig,
    
    # Utility Functions
    validate_persian_date, create_chunk_id, create_document_id,
    map_approval_authority, map_document_type
)

__all__ = [
    # Configuration
    'get_config', 'validate_config', 'OUTPUT_FILES', 'PROJECT_ROOT',
    
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

# ===============================================
# src/data_processing/__init__.py
# ===============================================
"""
Data processing modules for Legal Assistant
Handles document splitting, parsing, text processing, and chunking
"""

from .document_splitter import DocumentSplitter, split_legal_document, LawMetadata
from .document_parser import (
    LegalDocumentParser, parse_legal_documents,
    LegalSubsection as ParserSubsection,
    LegalNote as ParserNote,
    LegalArticle as ParserArticle,
    LegalChapter as ParserChapter,
    ParsedLegalDocument
)
from .text_processor import AdvancedTextProcessor, process_legal_documents
from .chunker import IntelligentChunker, chunk_legal_documents
from .metadata_generator import MetadataGenerator, generate_comprehensive_metadata

__all__ = [
    # Document Splitter
    'DocumentSplitter', 'split_legal_document', 'LawMetadata',
    
    # Document Parser
    'LegalDocumentParser', 'parse_legal_documents',
    'ParserSubsection', 'ParserNote', 'ParserArticle', 'ParserChapter',
    'ParsedLegalDocument',
    
    # Text Processor
    'AdvancedTextProcessor', 'process_legal_documents',
    
    # Chunker
    'IntelligentChunker', 'chunk_legal_documents',
    
    # Metadata Generator
    'MetadataGenerator', 'generate_comprehensive_metadata'
]

# ===============================================
# src/utils/__init__.py
# ===============================================
"""
Utility modules for Legal Assistant
Contains text processing and helper functions
"""

from .text_utils import (
    PersianTextProcessor, 
    clean_persian_text, 
    extract_persian_keywords, 
    normalize_text
)

__all__ = [
    'PersianTextProcessor', 
    'clean_persian_text',
    'extract_persian_keywords', 
    'normalize_text'
]

# ===============================================
# src/rag/__init__.py
# ===============================================
"""
RAG (Retrieval-Augmented Generation) modules for Legal Assistant
Contains embedding, vector store, retrieval, and LLM interface components

Note: This package will be implemented in Phase 2
"""

# Placeholder for Phase 2 development
__version__ = "0.0.0"
__status__ = "planned"

# Future imports (to be implemented in Phase 2)
# from .embedding_manager import EmbeddingManager
# from .vector_store import VectorStore
# from .retriever import LegalRetriever
# from .rag_pipeline import LegalRAGPipeline

__all__ = []

def get_phase_info():
    """Get information about RAG module development status"""
    return {
        "phase": 2,
        "status": "not_implemented",
        "description": "RAG functionality will be available in Phase 2",
        "planned_modules": [
            "embedding_manager.py",
            "vector_store.py", 
            "retriever.py",
            "rag_pipeline.py"
        ]
    }

# ===============================================
# src/comparison/__init__.py
# ===============================================
"""
Document comparison modules for Legal Assistant
Contains similarity analysis and document comparison tools

Note: This package will be implemented in Phase 3
"""

# Placeholder for Phase 3 development
__version__ = "0.0.0"
__status__ = "planned"

# Future imports (to be implemented in Phase 3)
# from .document_comparator import DocumentComparator
# from .similarity_analyzer import SimilarityAnalyzer

__all__ = []

def get_phase_info():
    """Get information about comparison module development status"""
    return {
        "phase": 3,
        "status": "not_implemented", 
        "description": "Document comparison functionality will be available in Phase 3",
        "planned_modules": [
            "document_comparator.py",
            "similarity_analyzer.py"
        ]
    }

# ===============================================
# src/llm/__init__.py
# ===============================================
"""
LLM interface modules for Legal Assistant
Contains prompt templates, response generation, and LLM communication

Note: This package will be implemented in Phase 2
"""

# Placeholder for Phase 2 development
__version__ = "0.0.0"
__status__ = "planned"

# Future imports (to be implemented in Phase 2)
# from .llm_interface import LLMInterface
# from .prompt_templates import LegalPromptTemplates
# from .response_generator import ResponseGenerator

__all__ = []

def get_phase_info():
    """Get information about LLM module development status"""
    return {
        "phase": 2,
        "status": "not_implemented",
        "description": "LLM interface functionality will be available in Phase 2", 
        "planned_modules": [
            "llm_interface.py",
            "prompt_templates.py",
            "response_generator.py"
        ]
    }