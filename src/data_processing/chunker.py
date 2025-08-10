# src/data_processing/chunker.py
"""
Intelligent text chunker for Legal Assistant
Creates optimal chunks for RAG while preserving legal document structure
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json
from pathlib import Path

from ..core.config import DOCUMENT_CONFIG
from ..core.models import (
    LegalDocument, TextChunk, ProcessingReport, ProcessingStatus,
    LegalArticle, LegalChapter, LegalNote, LegalSubsection,
    create_chunk_id
)
from ..utils.text_utils import PersianTextProcessor


class IntelligentChunker:
    """
    Intelligent chunker that preserves legal document structure
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DOCUMENT_CONFIG
        self.text_processor = PersianTextProcessor()
        
        # Chunking configuration
        self.min_chunk_size = self.config.get('min_chunk_size', 200)
        self.max_chunk_size = self.config.get('max_chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 100)
        
        # Processing statistics
        self.chunking_stats = {
            'documents_chunked': 0,
            'total_chunks_created': 0,
            'article_chunks': 0,
            'note_chunks': 0,
            'subsection_chunks': 0,
            'combined_chunks': 0,
            'oversized_chunks': 0,
            'undersized_chunks': 0
        }
    
    def calculate_chunk_priority(self, content_type: str, position: int) -> int:
        """
        Calculate priority for chunk ordering
        
        Args:
            content_type (str): Type of content (article, note, subsection)
            position (int): Position in document
            
        Returns:
            int: Priority score (higher = more important)
        """
        base_priority = {
            'article': 100,
            'single_article': 100,
            'note': 80,
            'subsection': 60,
            'chapter_title': 90,
            'footnote': 40
        }
        
        priority = base_priority.get(content_type, 50)
        
        # Earlier content gets slightly higher priority
        position_bonus = max(0, 50 - position)
        
        return priority + position_bonus
    
    def should_split_content(self, content: str) -> bool:
        """
        Determine if content should be split into smaller chunks
        
        Args:
            content (str): Content to evaluate
            
        Returns:
            bool: True if content should be split
        """
        return len(content) > self.max_chunk_size
    
    def can_combine_contents(self, content1: str, content2: str) -> bool:
        """
        Determine if two contents can be combined into one chunk
        
        Args:
            content1 (str): First content
            content2 (str): Second content
            
        Returns:
            bool: True if contents can be combined
        """
        combined_length = len(content1) + len(content2) + self.chunk_overlap
        return combined_length <= self.max_chunk_size
    
    def split_long_content(self, content: str, content_type: str) -> List[str]:
        """
        Split long content into smaller chunks while preserving meaning
        
        Args:
            content (str): Content to split
            content_type (str): Type of content
            
        Returns:
            List[str]: List of content chunks
        """
        if len(content) <= self.max_chunk_size:
            return [content]
        
        chunks = []
        
        # Try to split by sentences first
        sentences = self.text_processor.split_sentences(content)
        
        if len(sentences) > 1:
            current_chunk = ""
            
            for sentence in sentences:
                # Check if adding this sentence would exceed max size
                potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
                
                if len(potential_chunk) <= self.max_chunk_size:
                    current_chunk = potential_chunk
                else:
                    # Save current chunk if it's not empty
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    
                    # Start new chunk with current sentence
                    if len(sentence) <= self.max_chunk_size:
                        current_chunk = sentence
                    else:
                        # If single sentence is too long, split by words
                        word_chunks = self.split_by_words(sentence)
                        chunks.extend(word_chunks[:-1])
                        current_chunk = word_chunks[-1] if word_chunks else ""
            
            # Add remaining chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        else:
            # Single sentence/paragraph - split by words
            chunks = self.split_by_words(content)
        
        # Add overlap between chunks
        overlapped_chunks = self.add_overlap_to_chunks(chunks)
        
        return overlapped_chunks
    
    def split_by_words(self, content: str) -> List[str]:
        """
        Split content by words when sentence splitting is not sufficient
        
        Args:
            content (str): Content to split
            
        Returns:
            List[str]: List of word-based chunks
        """
        words = content.split()
        chunks = []
        current_chunk_words = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length <= self.max_chunk_size:
                current_chunk_words.append(word)
                current_length += word_length
            else:
                # Save current chunk
                if current_chunk_words:
                    chunks.append(' '.join(current_chunk_words))
                
                # Start new chunk
                current_chunk_words = [word]
                current_length = word_length
        
        # Add remaining words
        if current_chunk_words:
            chunks.append(' '.join(current_chunk_words))
        
        return chunks
    
    def add_overlap_to_chunks(self, chunks: List[str]) -> List[str]:
        """
        Add overlap between consecutive chunks
        
        Args:
            chunks (List[str]): Original chunks
            
        Returns:
            List[str]: Chunks with overlap
        """
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk - no prefix overlap needed
                overlapped_chunks.append(chunk)
            else:
                # Get overlap from previous chunk
                prev_chunk = chunks[i-1]
                
                # Extract last portion of previous chunk for overlap
                overlap_words = prev_chunk.split()[-self.chunk_overlap//10:]  # Rough word estimate
                overlap_text = ' '.join(overlap_words)
                
                # Combine with current chunk
                if len(overlap_text) + len(chunk) <= self.max_chunk_size:
                    combined_chunk = overlap_text + " " + chunk
                    overlapped_chunks.append(combined_chunk)
                else:
                    # If overlap would make chunk too large, use original
                    overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def create_chunk_metadata(self, source_element: str, element_type: str, 
                            document_id: str, position: int) -> Dict:
        """
        Create metadata for a chunk
        
        Args:
            source_element (str): Source element identifier
            element_type (str): Type of source element
            document_id (str): Source document ID
            position (int): Position in document
            
        Returns:
            Dict: Chunk metadata
        """
        return {
            'source_element': source_element,
            'element_type': element_type,
            'document_id': document_id,
            'position': position,
            'priority': self.calculate_chunk_priority(element_type, position),
            'creation_time': datetime.now().isoformat()
        }
    
    def chunk_article(self, article: LegalArticle, document_id: str, 
                     position: int, base_chunk_id: str) -> List[TextChunk]:
        """
        Create chunks from a legal article
        
        Args:
            article (LegalArticle): Article to chunk
            document_id (str): Source document ID
            position (int): Article position in document
            base_chunk_id (str): Base ID for chunk numbering
            
        Returns:
            List[TextChunk]: Generated chunks
        """
        chunks = []
        chunk_counter = 0
        
        # Main article content
        if article.content:
            content_chunks = []
            
            # Include article title in first chunk if present
            if article.title:
                main_content = f"{article.number} - {article.title}\n\n{article.content}"
            else:
                main_content = f"{article.number}\n\n{article.content}"
            
            if self.should_split_content(main_content):
                content_chunks = self.split_long_content(main_content, 'article')
            else:
                content_chunks = [main_content]
            
            # Create chunks for main content
            for i, content in enumerate(content_chunks):
                chunk_id = f"{base_chunk_id}_{chunk_counter:03d}"
                
                chunk = TextChunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=content,
                    chunk_type='article',
                    position=position,
                    word_count=len(content.split()),
                    character_count=len(content),
                    keywords=article.keywords[:10],  # Take top keywords
                    legal_references=[article.number],
                    metadata=self.create_chunk_metadata(
                        article.number, 'article', document_id, position
                    )
                )
                
                chunks.append(chunk)
                chunk_counter += 1
                self.chunking_stats['article_chunks'] += 1
        
        # Article subsections
        for j, subsection in enumerate(article.subsections):
            if subsection.content:
                subsection_content = f"{article.number} - {subsection.type} {subsection.number}\n\n{subsection.content}"
                
                if self.should_split_content(subsection_content):
                    subsection_chunks = self.split_long_content(subsection_content, 'subsection')
                else:
                    subsection_chunks = [subsection_content]
                
                for content in subsection_chunks:
                    chunk_id = f"{base_chunk_id}_{chunk_counter:03d}"
                    
                    chunk = TextChunk(
                        id=chunk_id,
                        document_id=document_id,
                        content=content,
                        chunk_type='subsection',
                        position=position,
                        word_count=len(content.split()),
                        character_count=len(content),
                        keywords=subsection.keywords[:5],
                        legal_references=[article.number, f"بند {subsection.number}"],
                        metadata=self.create_chunk_metadata(
                            f"{article.number}_subsection_{j}", 'subsection', 
                            document_id, position
                        )
                    )
                    
                    chunks.append(chunk)
                    chunk_counter += 1
                    self.chunking_stats['subsection_chunks'] += 1
        
        # Article notes
        for k, note in enumerate(article.notes):
            if note.content:
                note_content = f"{article.number} - {note.number}\n\n{note.content}"
                
                if self.should_split_content(note_content):
                    note_chunks = self.split_long_content(note_content, 'note')
                else:
                    note_chunks = [note_content]
                
                for content in note_chunks:
                    chunk_id = f"{base_chunk_id}_{chunk_counter:03d}"
                    
                    chunk = TextChunk(
                        id=chunk_id,
                        document_id=document_id,
                        content=content,
                        chunk_type='note',
                        position=position,
                        word_count=len(content.split()),
                        character_count=len(content),
                        keywords=note.keywords[:5],
                        legal_references=[article.number, note.number],
                        metadata=self.create_chunk_metadata(
                            f"{article.number}_note_{k}", 'note', 
                            document_id, position
                        )
                    )
                    
                    chunks.append(chunk)
                    chunk_counter += 1
                    self.chunking_stats['note_chunks'] += 1
        
        return chunks
    
    def chunk_chapter(self, chapter: LegalChapter, document_id: str, 
                     position: int, base_chunk_id: str) -> List[TextChunk]:
        """
        Create chunks from a legal chapter
        
        Args:
            chapter (LegalChapter): Chapter to chunk
            document_id (str): Source document ID
            position (int): Chapter position in document
            base_chunk_id (str): Base ID for chunk numbering
            
        Returns:
            List[TextChunk]: Generated chunks
        """
        chunks = []
        chunk_counter = 0
        
        # Chapter title chunk
        if chapter.title:
            chapter_content = f"{chapter.number} - {chapter.title}"
            chunk_id = f"{base_chunk_id}_{chunk_counter:03d}"
            
            chunk = TextChunk(
                id=chunk_id,
                document_id=document_id,
                content=chapter_content,
                chunk_type='chapter_title',
                position=position,
                word_count=len(chapter_content.split()),
                character_count=len(chapter_content),
                keywords=self.text_processor.extract_keywords(chapter_content, max_keywords=5),
                legal_references=[chapter.number],
                metadata=self.create_chunk_metadata(
                    chapter.number, 'chapter_title', document_id, position
                )
            )
            
            chunks.append(chunk)
            chunk_counter += 1
        
        # Process articles in chapter
        for i, article in enumerate(chapter.articles):
            article_chunks = self.chunk_article(
                article, document_id, position + i + 1, 
                f"{base_chunk_id}_{chunk_counter}"
            )
            chunks.extend(article_chunks)
            chunk_counter += len(article_chunks)
        
        return chunks
    
    def chunk_document(self, document: LegalDocument) -> List[TextChunk]:
        """
        Create chunks from a complete legal document
        
        Args:
            document (LegalDocument): Document to chunk
            
        Returns:
            List[TextChunk]: Generated chunks
        """
        chunks = []
        position_counter = 0
        
        try:
            # Process chapters
            for i, chapter in enumerate(document.chapters):
                chapter_chunks = self.chunk_chapter(
                    chapter, document.id, position_counter, 
                    f"{document.id}_ch{i}"
                )
                chunks.extend(chapter_chunks)
                position_counter += len(chapter_chunks)
            
            # Process standalone articles
            for i, article in enumerate(document.standalone_articles):
                article_chunks = self.chunk_article(
                    article, document.id, position_counter, 
                    f"{document.id}_art{i}"
                )
                chunks.extend(article_chunks)
                position_counter += len(article_chunks)
            
            # Process footnotes
            if document.footnotes:
                footnotes_content = "\n\n".join([
                    f"پاورقی {i+1}: {footnote}" 
                    for i, footnote in enumerate(document.footnotes)
                ])
                
                if footnotes_content:
                    chunk_id = f"{document.id}_footnotes"
                    
                    chunk = TextChunk(
                        id=chunk_id,
                        document_id=document.id,
                        content=footnotes_content,
                        chunk_type='footnote',
                        position=position_counter,
                        word_count=len(footnotes_content.split()),
                        character_count=len(footnotes_content),
                        keywords=self.text_processor.extract_keywords(footnotes_content, max_keywords=5),
                        legal_references=["پاورقی"],
                        metadata=self.create_chunk_metadata(
                            'footnotes', 'footnote', document.id, position_counter
                        )
                    )
                    
                    chunks.append(chunk)
            
            self.chunking_stats['documents_chunked'] += 1
            self.chunking_stats['total_chunks_created'] += len(chunks)
            
            # Update chunk quality statistics
            for chunk in chunks:
                if chunk.character_count > self.max_chunk_size:
                    self.chunking_stats['oversized_chunks'] += 1
                elif chunk.character_count < self.min_chunk_size:
                    self.chunking_stats['undersized_chunks'] += 1
            
            return chunks
        
        except Exception as e:
            raise Exception(f"خطا در تقسیم سند {document.id}: {str(e)}")
    
    def chunk_documents_batch(self, documents: List[LegalDocument]) -> Tuple[List[TextChunk], ProcessingReport]:
        """
        Chunk multiple documents in batch
        
        Args:
            documents (List[LegalDocument]): Documents to chunk
            
        Returns:
            Tuple[List[TextChunk], ProcessingReport]: All chunks and processing report
        """
        start_time = datetime.now()
        
        report = ProcessingReport(
            operation_type="text_chunking",
            total_items=len(documents),
            status=ProcessingStatus.PROCESSING
        )
        
        all_chunks = []
        
        for i, document in enumerate(documents):
            try:
                document_chunks = self.chunk_document(document)
                all_chunks.extend(document_chunks)
                report.processed_items += 1
                
                print(f"✓ تقسیم شد ({i+1}/{len(documents)}): {document.title[:50]}... - {len(document_chunks)} chunk")
                
            except Exception as e:
                error_msg = f"خطا در تقسیم سند {document.id}: {str(e)}"
                report.errors.append(error_msg)
                report.failed_items += 1
                print(f"✗ خطا ({i+1}/{len(documents)}): {error_msg}")
        
        # Finalize report
        report.end_time = datetime.now()
        report.status = ProcessingStatus.COMPLETED
        report.statistics = self.chunking_stats.copy()
        
        return all_chunks, report
    
    def get_chunking_statistics(self) -> Dict:
        """
        Get chunking statistics
        
        Returns:
            Dict: Chunking statistics
        """
        stats = self.chunking_stats.copy()
        
        # Add quality metrics
        if stats['total_chunks_created'] > 0:
            stats['quality_metrics'] = {
                'average_chunk_size': stats.get('total_characters', 0) / stats['total_chunks_created'],
                'oversized_percentage': (stats['oversized_chunks'] / stats['total_chunks_created']) * 100,
                'undersized_percentage': (stats['undersized_chunks'] / stats['total_chunks_created']) * 100,
            }
        
        return stats
    
    def export_chunks(self, chunks: List[TextChunk], output_file: str) -> None:
        """
        Export chunks to JSON file
        
        Args:
            chunks (List[TextChunk]): Chunks to export
            output_file (str): Output file path
        """
        chunks_data = {
            'metadata': {
                'total_chunks': len(chunks),
                'creation_date': datetime.now().isoformat(),
                'chunking_config': {
                    'min_size': self.min_chunk_size,
                    'max_size': self.max_chunk_size,
                    'overlap': self.chunk_overlap
                }
            },
            'chunks': [chunk.dict() for chunk in chunks]
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ {len(chunks)} chunk در فایل ذخیره شد: {output_path}")


def chunk_legal_documents(documents: List[LegalDocument], config: Optional[Dict] = None) -> Tuple[List[TextChunk], ProcessingReport]:
    """
    Convenience function to chunk legal documents
    
    Args:
        documents (List[LegalDocument]): Documents to chunk
        config (Optional[Dict]): Chunking configuration
        
    Returns:
        Tuple[List[TextChunk], ProcessingReport]: Chunks and processing report
    """
    chunker = IntelligentChunker(config)
    return chunker.chunk_documents_batch(documents)


# Main execution for testing
if __name__ == "__main__":
    # Test chunking with sample data
    from ..core.models import LegalDocument, LegalArticle, DocumentType, ApprovalAuthority
    
    # Create sample document
    sample_article = LegalArticle(
        number="ماده ۱",
        title="تعاریف",
        content="در این قانون کلمات و عبارات زیر در معانی مشروح مقابل آنها به کار می‌روند: الف) دانشگاه: مؤسسه آموزش عالی که دارای مجوز رسمی از وزارت علوم، تحقیقات و فناوری است. ب) هیئت علمی: اعضای هیئت علمی شاغل در دانشگاه‌های کشور که دارای مدرک تحصیلی و تخصص لازم هستند."
    )
    
    sample_document = LegalDocument(
        id="test_doc_001",
        title="قانون نمونه برای تست",
        approval_date="01/01/1400",
        approval_authority=ApprovalAuthority.PARLIAMENT,
        document_type=DocumentType.LAW,
        standalone_articles=[sample_article]
    )
    
    # Test chunking
    chunker = IntelligentChunker()
    
    print("شروع تست تقسیم متن...")
    chunks = chunker.chunk_document(sample_document)
    
    print(f"\n✅ تست تکمیل شد:")
    print(f"   - تعداد chunks ایجاد شده: {len(chunks)}")
    print(f"   - آمار تقسیم: {chunker.get_chunking_statistics()}")
    
    # Display sample chunks
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\n--- Chunk {i+1} ---")
        print(f"ID: {chunk.id}")
        print(f"Type: {chunk.chunk_type}")
        print(f"Length: {chunk.character_count} chars")
        print(f"Content: {chunk.content[:100]}...")
        print(f"Keywords: {chunk.keywords}")