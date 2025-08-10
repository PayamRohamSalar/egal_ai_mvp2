# scripts/process_documents.py
"""
Main document processing script for Legal Assistant Phase 1
Orchestrates the complete document processing pipeline from raw DOCX to processed chunks
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import validate_config, get_config, OUTPUT_FILES
from src.data_processing.document_splitter import DocumentSplitter
from src.data_processing.document_parser import LegalDocumentParser
from src.data_processing.text_processor import AdvancedTextProcessor
from src.data_processing.chunker import IntelligentChunker
from src.data_processing.metadata_generator import MetadataGenerator
from src.core.models import LegalDocument, ProcessingReport, ProcessingStatus


class DocumentProcessingPipeline:
    """
    Complete document processing pipeline for Phase 1
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or get_config()
        self.pipeline_stats = {
            'start_time': datetime.now(),
            'end_time': None,
            'total_processing_time': 0,
            'phase_times': {},
            'total_documents': 0,
            'successful_documents': 0,
            'failed_documents': 0,
            'total_chunks': 0
        }
        
        # Initialize processors
        self.splitter = DocumentSplitter()
        self.parser = LegalDocumentParser()
        self.text_processor = AdvancedTextProcessor()
        self.chunker = IntelligentChunker()
        self.metadata_generator = MetadataGenerator()
    
    def phase_1_split_documents(self, input_file: str) -> List[Dict]:
        """
        Phase 1.1: Split main document into individual laws
        
        Args:
            input_file (str): Path to input DOCX file
            
        Returns:
            List[Dict]: Individual law metadata
        """
        print("\n" + "="*60)
        print("🔄 فاز ۱.۱: تفکیک خودکار قوانین")
        print("="*60)
        
        phase_start = datetime.now()
        
        try:
            # Split documents
            result = self.splitter.split_document(input_file)
            
            if not result['success']:
                raise Exception(result['error'])
            
            laws_data = result['laws']
            self.pipeline_stats['total_documents'] = len(laws_data)
            
            print(f"✅ تفکیک کامل شد: {len(laws_data)} قانون استخراج شد")
            
            # Record phase time
            phase_time = (datetime.now() - phase_start).total_seconds()
            self.pipeline_stats['phase_times']['split'] = phase_time
            
            return laws_data
        
        except Exception as e:
            print(f"❌ خطا در فاز تفکیک: {str(e)}")
            raise
    
    def phase_2_parse_documents(self, laws_data: List[Dict]) -> List[LegalDocument]:
        """
        Phase 1.2: Parse document structure
        
        Args:
            laws_data (List[Dict]): Individual law metadata
            
        Returns:
            List[LegalDocument]: Parsed documents
        """
        print("\n" + "="*60)
        print("🔄 فاز ۱.۲: تجزیه ساختار اسناد")
        print("="*60)
        
        phase_start = datetime.now()
        parsed_documents = []
        
        try:
            for i, law_data in enumerate(laws_data):
                try:
                    # Parse individual law
                    parsed_doc = self.parser.parse_document(law_data)
                    parsed_documents.append(parsed_doc)
                    
                    print(f"✓ تجزیه شد ({i+1}/{len(laws_data)}): {parsed_doc.title[:50]}...")
                    
                except Exception as e:
                    print(f"✗ خطا در تجزیه سند {i+1}: {str(e)}")
                    self.pipeline_stats['failed_documents'] += 1
            
            self.pipeline_stats['successful_documents'] = len(parsed_documents)
            
            print(f"✅ تجزیه کامل شد: {len(parsed_documents)} سند تجزیه شد")
            
            # Record phase time
            phase_time = (datetime.now() - phase_start).total_seconds()
            self.pipeline_stats['phase_times']['parse'] = phase_time
            
            return parsed_documents
        
        except Exception as e:
            print(f"❌ خطا در فاز تجزیه: {str(e)}")
            raise
    
    def phase_3_process_text(self, documents: List[LegalDocument]) -> List[LegalDocument]:
        """
        Phase 1.3: Process and clean text
        
        Args:
            documents (List[LegalDocument]): Parsed documents
            
        Returns:
            List[LegalDocument]: Processed documents
        """
        print("\n" + "="*60)
        print("🔄 فاز ۱.۳: پردازش و تمیزکاری متون")
        print("="*60)
        
        phase_start = datetime.now()
        
        try:
            # Process documents in batch
            processed_docs, report = self.text_processor.process_documents_batch(documents)
            
            print(f"✅ پردازش متن کامل شد:")
            print(f"   - موفق: {report.processed_items}")
            print(f"   - ناموفق: {report.failed_items}")
            
            # Record phase time
            phase_time = (datetime.now() - phase_start).total_seconds()
            self.pipeline_stats['phase_times']['text_process'] = phase_time
            
            return processed_docs
        
        except Exception as e:
            print(f"❌ خطا در فاز پردازش متن: {str(e)}")
            raise
    
    def phase_4_chunk_documents(self, documents: List[LegalDocument]) -> List:
        """
        Phase 1.4: Create intelligent chunks
        
        Args:
            documents (List[LegalDocument]): Processed documents
            
        Returns:
            List[TextChunk]: Generated chunks
        """
        print("\n" + "="*60)
        print("🔄 فاز ۱.۴: تقسیم هوشمند متون")
        print("="*60)
        
        phase_start = datetime.now()
        
        try:
            # Chunk documents in batch
            chunks, report = self.chunker.chunk_documents_batch(documents)
            
            self.pipeline_stats['total_chunks'] = len(chunks)
            
            print(f"✅ تقسیم متن کامل شد:")
            print(f"   - اسناد پردازش شده: {report.processed_items}")
            print(f"   - کل chunks ایجاد شده: {len(chunks)}")
            
            # Record phase time
            phase_time = (datetime.now() - phase_start).total_seconds()
            self.pipeline_stats['phase_times']['chunk'] = phase_time
            
            return chunks
        
        except Exception as e:
            print(f"❌ خطا در فاز تقسیم متن: {str(e)}")
            raise
    
    def phase_5_generate_metadata(self, documents: List[LegalDocument], chunks: List) -> Dict:
        """
        Phase 1.5: Generate comprehensive metadata
        
        Args:
            documents (List[LegalDocument]): Processed documents
            chunks (List[TextChunk]): Generated chunks
            
        Returns:
            Dict: Comprehensive metadata
        """
        print("\n" + "="*60)
        print("🔄 فاز ۱.۵: تولید اطلاعات کمکی")
        print("="*60)
        
        phase_start = datetime.now()
        
        try:
            # Generate comprehensive metadata
            metadata_summary = self.metadata_generator.generate_processing_summary(documents, chunks)
            
            # Update document metadata
            for doc in documents:
                doc.metadata = self.metadata_generator.generate_document_metadata(doc)
            
            print(f"✅ تولید metadata کامل شد:")
            print(f"   - کیفیت متوسط: {metadata_summary['quality_statistics']['average_quality']:.2f}")
            print(f"   - اسناد با کیفیت بالا: {metadata_summary['quality_statistics']['high_quality_documents']}")
            
            # Record phase time
            phase_time = (datetime.now() - phase_start).total_seconds()
            self.pipeline_stats['phase_times']['metadata'] = phase_time
            
            return metadata_summary
        
        except Exception as e:
            print(f"❌ خطا در فاز تولید metadata: {str(e)}")
            raise
    
    def save_results(self, documents: List[LegalDocument], chunks: List, metadata: Dict) -> None:
        """
        Save all processing results to files
        
        Args:
            documents (List[LegalDocument]): Processed documents
            chunks (List[TextChunk]): Generated chunks
            metadata (Dict): Processing metadata
        """
        print("\n" + "="*60)
        print("💾 ذخیره نتایج")
        print("="*60)
        
        try:
            # Save processed documents
            documents_data = {
                'metadata': {
                    'total_documents': len(documents),
                    'processing_date': datetime.now().isoformat(),
                    'pipeline_version': '1.0'
                },
                'documents': [doc.dict() for doc in documents]
            }
            
            with open(OUTPUT_FILES['processed_documents'], 'w', encoding='utf-8') as f:
                json.dump(documents_data, f, ensure_ascii=False, indent=2)
            print(f"✓ اسناد پردازش شده: {OUTPUT_FILES['processed_documents']}")
            
            # Save chunks
            chunks_data = {
                'metadata': {
                    'total_chunks': len(chunks),
                    'creation_date': datetime.now().isoformat(),
                    'chunking_config': {
                        'min_size': self.chunker.min_chunk_size,
                        'max_size': self.chunker.max_chunk_size,
                        'overlap': self.chunker.chunk_overlap
                    }
                },
                'chunks': [chunk.dict() for chunk in chunks]
            }
            
            with open(OUTPUT_FILES['chunks'], 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
            print(f"✓ Chunks: {OUTPUT_FILES['chunks']}")
            
            # Save metadata
            with open(OUTPUT_FILES['metadata'], 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"✓ Metadata: {OUTPUT_FILES['metadata']}")
            
            # Save final processing report
            self.save_final_report()
            
        except Exception as e:
            print(f"❌ خطا در ذخیره نتایج: {str(e)}")
            raise
    
    def save_final_report(self) -> None:
        """
        Save final processing report
        """
        self.pipeline_stats['end_time'] = datetime.now()
        self.pipeline_stats['total_processing_time'] = (
            self.pipeline_stats['end_time'] - self.pipeline_stats['start_time']
        ).total_seconds()
        
        # Create comprehensive report
        final_report = {
            'pipeline_summary': {
                'status': 'completed',
                'total_time': self.pipeline_stats['total_processing_time'],
                'phase_times': self.pipeline_stats['phase_times'],
                'success_rate': (
                    self.pipeline_stats['successful_documents'] / 
                    max(self.pipeline_stats['total_documents'], 1)
                ) * 100
            },
            'statistics': self.pipeline_stats,
            'processor_stats': {
                'splitter': self.splitter.processing_stats,
                'parser': self.parser.get_parsing_statistics(),
                'text_processor': self.text_processor.get_processing_statistics(),
                'chunker': self.chunker.get_chunking_statistics(),
                'metadata_generator': self.metadata_generator.generation_stats
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open(OUTPUT_FILES['processing_report'], 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        print(f"✓ گزارش نهایی: {OUTPUT_FILES['processing_report']}")
    
    def run_complete_pipeline(self, input_file: str) -> Dict:
        """
        Run the complete document processing pipeline
        
        Args:
            input_file (str): Path to input DOCX file
            
        Returns:
            Dict: Pipeline results
        """
        print("\n" + "🚀" + "="*58 + "🚀")
        print("    آغاز پردازش کامل اسناد حقوقی - فاز ۱")
        print("🚀" + "="*58 + "🚀")
        
        try:
            # Validate configuration
            if not validate_config():
                raise Exception("تنظیمات سیستم نامعتبر است")
            
            # Phase 1.1: Split documents
            laws_data = self.phase_1_split_documents(input_file)
            
            # Phase 1.2: Parse documents
            documents = self.phase_2_parse_documents(laws_data)
            
            # Phase 1.3: Process text
            processed_documents = self.phase_3_process_text(documents)
            
            # Phase 1.4: Create chunks
            chunks = self.phase_4_chunk_documents(processed_documents)
            
            # Phase 1.5: Generate metadata
            metadata = self.phase_5_generate_metadata(processed_documents, chunks)
            
            # Save all results
            self.save_results(processed_documents, chunks, metadata)
            
            # Print final summary
            self.print_final_summary()
            
            return {
                'success': True,
                'documents': len(processed_documents),
                'chunks': len(chunks),
                'processing_time': self.pipeline_stats['total_processing_time'],
                'metadata': metadata
            }
        
        except Exception as e:
            print(f"\n❌ خطا در پردازش pipeline: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': (datetime.now() - self.pipeline_stats['start_time']).total_seconds()
            }
    
    def print_final_summary(self) -> None:
        """
        Print final processing summary
        """
        print("\n" + "🎉" + "="*58 + "🎉")
        print("         خلاصه نهایی پردازش فاز ۱")
        print("🎉" + "="*58 + "🎉")
        
        print(f"\n📊 آمار کلی:")
        print(f"   ⏱️  زمان کل پردازش: {self.pipeline_stats['total_processing_time']:.2f} ثانیه")
        print(f"   📄 تعداد اسناد کل: {self.pipeline_stats['total_documents']}")
        print(f"   ✅ اسناد موفق: {self.pipeline_stats['successful_documents']}")
        print(f"   ❌ اسناد ناموفق: {self.pipeline_stats['failed_documents']}")
        print(f"   🧩 تعداد chunks: {self.pipeline_stats['total_chunks']}")
        
        print(f"\n⏱️  زمان هر فاز:")
        for phase, time_taken in self.pipeline_stats['phase_times'].items():
            print(f"   📋 {phase}: {time_taken:.2f} ثانیه")
        
        success_rate = (
            self.pipeline_stats['successful_documents'] / 
            max(self.pipeline_stats['total_documents'], 1)
        ) * 100
        
        print(f"\n🎯 نرخ موفقیت: {success_rate:.1f}%")
        
        print(f"\n📂 فایل‌های خروجی:")
        for file_type, file_path in OUTPUT_FILES.items():
            if file_path.exists():
                print(f"   ✅ {file_type}: {file_path}")
            else:
                print(f"   ❌ {file_type}: فایل ایجاد نشد")
        
        print("\n" + "="*60)
        print("🎊 فاز ۱ با موفقیت تکمیل شد! 🎊")
        print("="*60)


def main():
    """
    Main function for command line execution
    """
    parser = argparse.ArgumentParser(description='Legal Assistant Document Processing Pipeline')
    parser.add_argument('input_file', help='Path to input DOCX file (Part2_Legals.docx)')
    parser.add_argument('--output-dir', help='Output directory (default: data/processed)')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ فایل ورودی پیدا نشد: {input_path}")
        return 1
    
    if not input_path.suffix.lower() == '.docx':
        print(f"❌ فرمت فایل باید DOCX باشد: {input_path}")
        return 1
    
    try:
        # Load custom config if provided
        config = None
        if args.config:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # Initialize and run pipeline
        pipeline = DocumentProcessingPipeline(config)
        result = pipeline.run_complete_pipeline(str(input_path))
        
        if result['success']:
            print(f"\n🎉 پردازش با موفقیت تکمیل شد!")
            return 0
        else:
            print(f"\n💥 پردازش با خطا مواجه شد: {result['error']}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⏹️  پردازش توسط کاربر متوقف شد")
        return 1
    except Exception as e:
        print(f"\n💥 خطای غیرمنتظره: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())