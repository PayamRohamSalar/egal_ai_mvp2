# src/data_processing/document_parser.py
"""
Document parser for Legal Assistant
Analyzes and parses the internal structure of individual legal documents
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from ..core.config import DOCUMENT_CONFIG
from ..utils.text_utils import PersianTextProcessor


@dataclass
class LegalSubsection:
    """Represents a subsection within an article"""
    number: str
    content: str
    type: str  # 'numbered', 'lettered', 'dash'
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class LegalNote:
    """Represents a note (تبصره) within an article"""
    number: str
    content: str
    subsections: List[LegalSubsection] = None
    keywords: List[str] = None

    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.keywords is None:
            self.keywords = []


@dataclass
class LegalArticle:
    """Represents a legal article (ماده)"""
    number: str
    title: str
    content: str
    subsections: List[LegalSubsection] = None
    notes: List[LegalNote] = None
    keywords: List[str] = None
    word_count: Optional[int] = None

    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.notes is None:
            self.notes = []
        if self.keywords is None:
            self.keywords = []
        if self.word_count is None:
            self.word_count = len(self.content.split()) if self.content else 0


@dataclass
class LegalChapter:
    """Represents a chapter (فصل) in a legal document"""
    number: str
    title: str
    articles: List[LegalArticle] = None
    summary: Optional[str] = None

    def __post_init__(self):
        if self.articles is None:
            self.articles = []

    @property
    def article_count(self) -> int:
        """Get number of articles in chapter"""
        return len(self.articles)

    @property
    def total_word_count(self) -> int:
        """Get total word count for all articles in chapter"""
        return sum(article.word_count or 0 for article in self.articles)


@dataclass
class ParsedLegalDocument:
    """Complete parsed legal document structure"""
    id: str
    title: str
    approval_date: str
    approval_authority: str
    document_type: str  # قانون، آیین‌نامه، دستورالعمل، etc.
    chapters: List[LegalChapter] = None
    standalone_articles: List[LegalArticle] = None  # Articles not in chapters
    footnotes: List[str] = None
    metadata: Dict = None
    parsing_timestamp: str = None

    def __post_init__(self):
        if self.chapters is None:
            self.chapters = []
        if self.standalone_articles is None:
            self.standalone_articles = []
        if self.footnotes is None:
            self.footnotes = []
        if self.metadata is None:
            self.metadata = {}
        if self.parsing_timestamp is None:
            self.parsing_timestamp = datetime.now().isoformat()

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


class LegalDocumentParser:
    """
    Parses the internal structure of legal documents
    """
    
    def __init__(self):
        self.text_processor = PersianTextProcessor()
        self.parsing_stats = {
            'documents_parsed': 0,
            'articles_extracted': 0,
            'chapters_found': 0,
            'notes_extracted': 0,
            'parsing_errors': 0
        }
    
    def identify_document_type(self, title: str) -> str:
        """
        Identify the type of legal document
        
        Args:
            title (str): Document title
            
        Returns:
            str: Document type
        """
        title_lower = title.lower()
        
        if 'قانون' in title_lower:
            return 'قانون'
        elif 'آیین‌نامه' in title_lower or 'آیین نامه' in title_lower:
            return 'آیین‌نامه'
        elif 'دستورالعمل' in title_lower:
            return 'دستورالعمل'
        elif 'مصوبه' in title_lower:
            return 'مصوبه'
        elif 'بخشنامه' in title_lower:
            return 'بخشنامه'
        else:
            return 'نامشخص'
    
    def extract_chapters(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Extract chapters from document text
        
        Args:
            text (str): Document text
            
        Returns:
            List[Tuple]: List of (chapter_num, chapter_title, start_pos, end_pos)
        """
        chapters = []
        chapter_pattern = DOCUMENT_CONFIG["chapter_pattern"]
        
        # Find all chapter headers
        chapter_matches = list(re.finditer(chapter_pattern, text, re.MULTILINE))
        
        for i, match in enumerate(chapter_matches):
            chapter_num = match.group(1).strip()
            chapter_title = match.group(2).strip() if match.group(2) else ""
            start_pos = match.start()
            
            # Determine end position (start of next chapter or end of text)
            if i + 1 < len(chapter_matches):
                end_pos = chapter_matches[i + 1].start()
            else:
                end_pos = len(text)
            
            chapters.append((chapter_num, chapter_title, start_pos, end_pos))
        
        return chapters
    
    def extract_articles(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Extract articles from text
        
        Args:
            text (str): Text to extract articles from
            
        Returns:
            List[Tuple]: List of (article_num, article_title, start_pos, end_pos)
        """
        articles = []
        
        # Patterns for different article types
        article_pattern = DOCUMENT_CONFIG["article_pattern"]
        single_article_pattern = DOCUMENT_CONFIG["single_article_pattern"]
        
        # Find regular articles
        article_matches = list(re.finditer(article_pattern, text, re.MULTILINE))
        
        # Find single articles (ماده واحده)
        single_matches = list(re.finditer(single_article_pattern, text, re.MULTILINE))
        
        # Combine and sort all matches
        all_matches = [(m, 'regular') for m in article_matches] + [(m, 'single') for m in single_matches]
        all_matches.sort(key=lambda x: x[0].start())
        
        for i, (match, article_type) in enumerate(all_matches):
            if article_type == 'single':
                article_num = match.group(1).strip()
                article_title = ""
            else:
                article_num = match.group(1).strip()
                article_title = match.group(2).strip() if match.group(2) else ""
            
            start_pos = match.start()
            
            # Determine end position
            if i + 1 < len(all_matches):
                end_pos = all_matches[i + 1][0].start()
            else:
                end_pos = len(text)
            
            articles.append((article_num, article_title, start_pos, end_pos))
        
        return articles
    
    def extract_subsections(self, article_text: str) -> List[LegalSubsection]:
        """
        Extract subsections from article text
        
        Args:
            article_text (str): Article text
            
        Returns:
            List[LegalSubsection]: List of subsections
        """
        subsections = []
        
        # Patterns for different subsection types
        patterns = [
            (r'^([۰-۹]+)\s*[-–—]\s*(.+?)(?=^[۰-۹]+\s*[-–—]|\Z)', 'numbered'),
            (r'^([الف-ی]+)\s*[-–—]\s*(.+?)(?=^[الف-ی]+\s*[-–—]|\Z)', 'lettered'),
            (r'^[-–—]\s*(.+?)(?=^[-–—]|\Z)', 'dash')
        ]
        
        for pattern, subsection_type in patterns:
            matches = re.finditer(pattern, article_text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                if subsection_type == 'dash':
                    number = '-'
                    content = match.group(1).strip()
                else:
                    number = match.group(1).strip()
                    content = match.group(2).strip()
                
                if content:
                    # Extract keywords for subsection
                    keywords = self.text_processor.extract_keywords(content, max_keywords=5)
                    
                    subsections.append(LegalSubsection(
                        number=number,
                        content=content,
                        type=subsection_type,
                        keywords=keywords
                    ))
        
        # Sort subsections by their position in text
        return sorted(subsections, key=lambda x: article_text.find(x.content))
    
    def extract_notes(self, article_text: str) -> List[LegalNote]:
        """
        Extract notes (تبصره) from article text
        
        Args:
            article_text (str): Article text
            
        Returns:
            List[LegalNote]: List of notes
        """
        notes = []
        note_pattern = DOCUMENT_CONFIG["note_pattern"]
        
        # Find all note matches
        note_matches = list(re.finditer(note_pattern, article_text, re.MULTILINE))
        
        for i, match in enumerate(note_matches):
            note_num = match.group(1).strip()
            note_start = match.start()
            
            # Determine note end position
            if i + 1 < len(note_matches):
                note_end = note_matches[i + 1].start()
            else:
                note_end = len(article_text)
            
            note_text = article_text[note_start:note_end].strip()
            
            # Remove the note header from content
            note_content = re.sub(note_pattern, '', note_text, count=1).strip()
            
            # Extract subsections within the note
            note_subsections = self.extract_subsections(note_content)
            
            # Extract keywords for note
            keywords = self.text_processor.extract_keywords(note_content, max_keywords=5)
            
            notes.append(LegalNote(
                number=note_num,
                content=note_content,
                subsections=note_subsections,
                keywords=keywords
            ))
        
        return notes
    
    def extract_footnotes(self, text: str) -> List[str]:
        """
        Extract footnotes from document text
        
        Args:
            text (str): Document text
            
        Returns:
            List[str]: List of footnotes
        """
        footnotes = []
        footnote_pattern = DOCUMENT_CONFIG["footnote_pattern"]
        
        # Find footnote references
        footnote_matches = re.finditer(footnote_pattern + r'(.+?)(?=\(\d+\)|\Z)', text, re.DOTALL)
        
        for match in footnote_matches:
            footnote_text = match.group(1).strip()
            if footnote_text:
                footnotes.append(footnote_text)
        
        return footnotes
    
    def parse_article(self, article_text: str, article_num: str, article_title: str) -> LegalArticle:
        """
        Parse a single article
        
        Args:
            article_text (str): Article text
            article_num (str): Article number
            article_title (str): Article title
            
        Returns:
            LegalArticle: Parsed article
        """
        # Clean the article text
        cleaned_text = self.text_processor.clean_text(article_text)
        
        # Remove the article header from content
        content_text = re.sub(DOCUMENT_CONFIG["article_pattern"], '', cleaned_text, count=1)
        content_text = re.sub(DOCUMENT_CONFIG["single_article_pattern"], '', content_text, count=1)
        content_text = content_text.strip()
        
        # Extract components
        subsections = self.extract_subsections(content_text)
        notes = self.extract_notes(content_text)
        
        # Extract main article content (excluding subsections and notes)
        main_content = content_text
        
        # Remove subsections and notes from main content
        for note in notes:
            main_content = main_content.replace(note.content, '')
        for subsection in subsections:
            main_content = main_content.replace(subsection.content, '')
        
        main_content = re.sub(r'\s+', ' ', main_content).strip()
        
        # Extract keywords
        keywords = self.text_processor.extract_keywords(cleaned_text, max_keywords=10)
        
        return LegalArticle(
            number=article_num,
            title=article_title,
            content=main_content,
            subsections=subsections,
            notes=notes,
            keywords=keywords
        )
    
    def parse_chapter(self, chapter_text: str, chapter_num: str, chapter_title: str) -> LegalChapter:
        """
        Parse a single chapter
        
        Args:
            chapter_text (str): Chapter text
            chapter_num (str): Chapter number
            chapter_title (str): Chapter title
            
        Returns:
            LegalChapter: Parsed chapter
        """
        articles = []
        
        # Extract articles within this chapter
        article_data = self.extract_articles(chapter_text)
        
        for article_num, article_title, start_pos, end_pos in article_data:
            article_text = chapter_text[start_pos:end_pos]
            article = self.parse_article(article_text, article_num, article_title)
            articles.append(article)
            self.parsing_stats['articles_extracted'] += 1
        
        return LegalChapter(
            number=chapter_num,
            title=chapter_title,
            articles=articles
        )
    
    def parse_document_from_dict(self, law_dict: Dict) -> ParsedLegalDocument:
        """
        Parse a complete legal document from dictionary format
        
        Args:
            law_dict (Dict): Law dictionary with raw_content
            
        Returns:
            ParsedLegalDocument: Completely parsed document
        """
        try:
            text = law_dict.get('raw_content', '')
            if not text:
                raise ValueError("No raw_content found in document")
            
            # Identify document type
            doc_type = self.identify_document_type(law_dict.get('title', ''))
            
            # Extract chapters
            chapter_data = self.extract_chapters(text)
            chapters = []
            
            processed_ranges = []  # Track processed text ranges
            
            for chapter_num, chapter_title, start_pos, end_pos in chapter_data:
                chapter_text = text[start_pos:end_pos]
                chapter = self.parse_chapter(chapter_text, chapter_num, chapter_title)
                chapters.append(chapter)
                processed_ranges.append((start_pos, end_pos))
                self.parsing_stats['chapters_found'] += 1
            
            # Extract standalone articles (not in chapters)
            standalone_articles = []
            
            # If no chapters found, treat all articles as standalone
            if not chapters:
                article_data = self.extract_articles(text)
                for article_num, article_title, start_pos, end_pos in article_data:
                    article_text = text[start_pos:end_pos]
                    article = self.parse_article(article_text, article_num, article_title)
                    standalone_articles.append(article)
                    self.parsing_stats['articles_extracted'] += 1
            
            # Extract footnotes
            footnotes = self.extract_footnotes(text)
            
            # Count notes
            for chapter in chapters:
                for article in chapter.articles:
                    self.parsing_stats['notes_extracted'] += len(article.notes)
            
            for article in standalone_articles:
                self.parsing_stats['notes_extracted'] += len(article.notes)
            
            # Create metadata
            metadata = {
                'word_count': len(text.split()),
                'character_count': len(text),
                'structure_type': 'با فصل' if chapters else 'بدون فصل',
                'has_footnotes': len(footnotes) > 0,
                'complexity_score': self.calculate_complexity_score(chapters, standalone_articles),
                'original_quality_score': law_dict.get('quality_score', 0.0)
            }
            
            parsed_doc = ParsedLegalDocument(
                id=law_dict.get('id', ''),
                title=law_dict.get('title', ''),
                approval_date=law_dict.get('approval_date', ''),
                approval_authority=law_dict.get('approval_authority', ''),
                document_type=doc_type,
                chapters=chapters,
                standalone_articles=standalone_articles,
                footnotes=footnotes,
                metadata=metadata
            )
            
            self.parsing_stats['documents_parsed'] += 1
            return parsed_doc
        
        except Exception as e:
            self.parsing_stats['parsing_errors'] += 1
            raise Exception(f"خطا در تجزیه سند {law_dict.get('id', 'نامشخص')}: {str(e)}")
    
    def calculate_complexity_score(self, chapters: List[LegalChapter], standalone_articles: List[LegalArticle]) -> float:
        """
        Calculate document complexity score
        
        Args:
            chapters (List[LegalChapter]): Document chapters
            standalone_articles (List[LegalArticle]): Standalone articles
            
        Returns:
            float: Complexity score (0.0 to 1.0)
        """
        score = 0.0
        
        # Chapter complexity
        if chapters:
            score += 0.3
            score += min(len(chapters) * 0.1, 0.2)
        
        # Article complexity
        total_articles = len(standalone_articles) + sum(len(ch.articles) for ch in chapters)
        score += min(total_articles * 0.05, 0.3)
        
        # Subsection and note complexity
        total_subsections = 0
        total_notes = 0
        
        for article in standalone_articles:
            total_subsections += len(article.subsections)
            total_notes += len(article.notes)
        
        for chapter in chapters:
            for article in chapter.articles:
                total_subsections += len(article.subsections)
                total_notes += len(article.notes)
        
        score += min(total_subsections * 0.02, 0.1)
        score += min(total_notes * 0.03, 0.1)
        
        return min(score, 1.0)
    
    def parse_documents_batch(self, input_file: str, output_file: str = None) -> List[ParsedLegalDocument]:
        """
        Parse multiple legal documents from individual laws file
        
        Args:
            input_file (str): Path to individual laws JSON file
            output_file (str): Optional output file path
            
        Returns:
            List[ParsedLegalDocument]: List of parsed documents
        """
        parsed_documents = []
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            laws = data.get('laws', [])
            print(f"در حال تجزیه {len(laws)} سند حقوقی...")
            
            for i, law_dict in enumerate(laws):
                try:
                    parsed_doc = self.parse_document_from_dict(law_dict)
                    parsed_documents.append(parsed_doc)
                    print(f"✓ تجزیه شد ({i+1}/{len(laws)}): {parsed_doc.title[:50]}...")
                except Exception as e:
                    print(f"✗ خطا در تجزیه ({i+1}/{len(laws)}): {str(e)}")
            
            # Save results if output file specified
            if output_file:
                self.save_parsed_documents(parsed_documents, output_file)
            
            print(f"\n✅ تجزیه کامل شد:")
            stats = self.get_parsing_statistics()
            print(f"   - اسناد تجزیه شده: {stats['documents_parsed']}")
            print(f"   - مواد استخراج شده: {stats['articles_extracted']}")
            print(f"   - فصل‌های پیدا شده: {stats['chapters_found']}")
            print(f"   - تبصره‌های استخراج شده: {stats['notes_extracted']}")
            
            return parsed_documents
        
        except Exception as e:
            print(f"خطا در بارگذاری فایل قوانین: {str(e)}")
            return []
    
    def save_parsed_documents(self, parsed_docs: List[ParsedLegalDocument], output_file: str) -> None:
        """
        Save parsed documents to JSON file
        
        Args:
            parsed_docs (List[ParsedLegalDocument]): Parsed documents
            output_file (str): Output file path
        """
        try:
            output_data = {
                'metadata': {
                    'total_documents': len(parsed_docs),
                    'parsing_date': datetime.now().isoformat(),
                    'parsing_stats': self.parsing_stats
                },
                'documents': [asdict(doc) for doc in parsed_docs]
            }
            
            output_path = Path(output_file)
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ اسناد تجزیه شده ذخیره شدند: {output_path}")
        
        except Exception as e:
            print(f"خطا در ذخیره اسناد تجزیه شده: {str(e)}")
    
    def get_parsing_statistics(self) -> Dict:
        """
        Get parsing statistics
        
        Returns:
            Dict: Parsing statistics
        """
        return self.parsing_stats.copy()


def parse_legal_documents(input_file: str, output_file: str = None) -> List[ParsedLegalDocument]:
    """
    Convenience function to parse legal documents from individual laws file
    
    Args:
        input_file (str): Path to individual laws JSON file
        output_file (str): Optional output file path
        
    Returns:
        List[ParsedLegalDocument]: List of parsed documents
    """
    parser = LegalDocumentParser()
    return parser.parse_documents_batch(input_file, output_file)


# Main execution for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Test with individual laws file
    laws_file = Path("data/processed/individual_laws.json")
    
    if len(sys.argv) > 1:
        laws_file = Path(sys.argv[1])
    
    if laws_file.exists():
        print(f"شروع تجزیه اسناد از فایل: {laws_file}")
        parsed_docs = parse_legal_documents(str(laws_file), "data/processed/parsed_documents.json")
        
        if parsed_docs:
            print(f"\n✅ {len(parsed_docs)} سند با موفقیت تجزیه شد")
            
            # Display sample results
            for doc in parsed_docs[:2]:  # Show first 2 documents
                print(f"\n--- {doc.title} ---")
                print(f"نوع: {doc.document_type}")
                print(f"فصل‌ها: {len(doc.chapters)}")
                print(f"مواد مستقل: {len(doc.standalone_articles)}")
                print(f"کل مواد: {doc.total_articles}")
                print(f"پیچیدگی: {doc.metadata.get('complexity_score', 0):.2f}")
        else:
            print("❌ هیچ سندی تجزیه نشد")
    else:
        print(f"❌ فایل پیدا نشد: {laws_file}")
        print("ابتدا فاز تفکیک اسناد را اجرا کنید.")