"""
Document organization logic for DocMerge.
Handles categorization, sorting, and merging of documents.
"""

import os
import re
import shutil
from pathlib import Path
from io import BytesIO
from typing import Optional

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, LETTER

from .converter import (
    convert_image_to_pdf_bytes,
    convert_docx_to_pdf_bytes,
    create_title_page,
    is_supported_file,
    get_file_type,
    IMAGE_EXTENSIONS
)

# System files to always exclude
SYSTEM_FILE_PATTERNS = [
    r'\.DS_Store$',
    r'desktop\.ini$',
    r'Thumbs\.db$',
    r'\.gitignore$',
    r'\.git/',
    r'__pycache__',
    r'\.pyc$',
]


class DocumentOrganizer:
    """Main class for organizing and merging documents."""
    
    def __init__(
        self,
        source_dir: str,
        output_dir: str,
        group_size: int = 3,
        page_size: str = "A4",
        add_title_pages: bool = True,
        add_source_labels: bool = True,
        verbose: bool = True
    ):
        """
        Initialize the document organizer.
        
        Args:
            source_dir: Directory containing documents to organize
            output_dir: Directory for output PDFs
            group_size: Number of categories to combine per merged PDF
            page_size: Page size ("A4" or "LETTER")
            add_title_pages: Add title pages to each section
            add_source_labels: Add source labels to converted images
            verbose: Print progress messages
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.group_size = group_size
        self.page_size = A4 if page_size.upper() == "A4" else LETTER
        self.add_title_pages = add_title_pages
        self.add_source_labels = add_source_labels
        self.verbose = verbose
        
        self.individual_dir = self.output_dir / "Individual"
        self.combined_dir = self.output_dir / "Combined"
        self.set_aside_dir = self.output_dir / "Set_Aside"
        
        self.set_aside_files = []
        self.processing_log = []
        self.categories = []
    
    def log(self, message: str):
        """Log a message."""
        if self.verbose:
            print(message)
        self.processing_log.append(message)
    
    def is_system_file(self, filename: str) -> bool:
        """Check if file is a system file to exclude."""
        for pattern in SYSTEM_FILE_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False
    
    def extract_sort_key(self, filename: str) -> tuple:
        """Extract sorting key from filename."""
        # Match leading numbers like "1)", "1.", "01-", etc.
        match = re.match(r'^(\d+)[\)\.\s\-_]', filename)
        num = int(match.group(1)) if match else 999
        alpha_part = re.sub(r'^[\d\)\.\s\-_]+', '', filename).lower()
        return (num, alpha_part, filename)
    
    def discover_categories(self) -> list[tuple[str, Path]]:
        """
        Discover document categories from source directory.
        Categories are subdirectories, or the source dir itself if no subdirs.
        
        Returns:
            List of (category_name, category_path) tuples
        """
        categories = []
        
        # Check for subdirectories
        subdirs = [d for d in self.source_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if subdirs:
            # Sort subdirectories intelligently
            subdirs_sorted = sorted(subdirs, key=lambda d: self.extract_sort_key(d.name))
            for subdir in subdirs_sorted:
                categories.append((subdir.name, subdir))
        else:
            # Use source directory as single category
            categories.append((self.source_dir.name, self.source_dir))
        
        self.categories = categories
        return categories
    
    def get_files_in_category(self, category_path: Path) -> list[Path]:
        """
        Get all processable files in a category, sorted logically.
        
        Args:
            category_path: Path to the category directory
        
        Returns:
            Sorted list of file paths
        """
        files = []
        
        for item in category_path.rglob('*'):
            if item.is_file():
                if self.is_system_file(item.name):
                    self.set_aside_files.append((item, "System file"))
                elif is_supported_file(str(item)):
                    files.append(item)
                else:
                    self.set_aside_files.append((item, f"Unsupported format: {item.suffix}"))
        
        # Sort files
        return sorted(files, key=lambda f: self.extract_sort_key(f.name))
    
    def process_file(self, file_path: Path, pdf_writer: PdfWriter) -> bool:
        """
        Process a single file and add to PDF writer.
        
        Args:
            file_path: Path to the file
            pdf_writer: PdfWriter to add pages to
        
        Returns:
            True if successful
        """
        file_type = get_file_type(str(file_path))
        filename = file_path.name
        
        try:
            if file_type == 'pdf':
                reader = PdfReader(str(file_path))
                for page in reader.pages:
                    pdf_writer.add_page(page)
                self.log(f"  Added PDF: {filename} ({len(reader.pages)} pages)")
                return True
                
            elif file_type == 'image':
                pdf_bytes = convert_image_to_pdf_bytes(
                    str(file_path),
                    add_source_label=self.add_source_labels,
                    page_size=self.page_size
                )
                if pdf_bytes:
                    reader = PdfReader(BytesIO(pdf_bytes))
                    for page in reader.pages:
                        pdf_writer.add_page(page)
                    self.log(f"  Added image: {filename}")
                    return True
                    
            elif file_type == 'docx':
                pdf_bytes = convert_docx_to_pdf_bytes(str(file_path), page_size=self.page_size)
                if pdf_bytes:
                    reader = PdfReader(BytesIO(pdf_bytes))
                    for page in reader.pages:
                        pdf_writer.add_page(page)
                    self.log(f"  Added DOCX: {filename}")
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"  ERROR processing {filename}: {e}")
            return False
    
    def process_category(self, category_name: str, category_path: Path, index: int) -> Optional[Path]:
        """
        Process all files in a category and create a single PDF.
        
        Args:
            category_name: Name of the category
            category_path: Path to the category directory
            index: Category index (1-based)
        
        Returns:
            Path to created PDF or None
        """
        self.log(f"\nProcessing: {category_name}")
        
        files = self.get_files_in_category(category_path)
        if not files:
            self.log(f"  No supported files found")
            return None
        
        pdf_writer = PdfWriter()
        
        # Add title page
        if self.add_title_pages:
            title_pdf = create_title_page(
                category_name,
                f"Section {index}",
                page_size=self.page_size
            )
            title_reader = PdfReader(BytesIO(title_pdf))
            pdf_writer.add_page(title_reader.pages[0])
        
        # Process files
        processed = 0
        for file_path in files:
            if self.process_file(file_path, pdf_writer):
                processed += 1
        
        if processed == 0:
            self.log(f"  No files successfully processed")
            return None
        
        # Save PDF
        safe_name = re.sub(r'[^\w\s-]', '', category_name).strip().replace(' ', '_')
        output_path = self.individual_dir / f"{index:02d}_{safe_name}.pdf"
        
        with open(output_path, 'wb') as f:
            pdf_writer.write(f)
        
        self.log(f"  Created: {output_path.name} ({len(pdf_writer.pages)} pages, {processed} files)")
        return output_path
    
    def create_combined_pdfs(self, individual_pdfs: list[Path]):
        """
        Create combined PDFs from individual category PDFs.
        
        Args:
            individual_pdfs: List of paths to individual PDFs
        """
        if not individual_pdfs or self.group_size <= 0:
            return
        
        self.log(f"\n{'='*60}")
        self.log(f"Creating combined PDFs ({self.group_size} sections per PDF)")
        self.log('='*60)
        
        for i in range(0, len(individual_pdfs), self.group_size):
            group = individual_pdfs[i:i + self.group_size]
            start_idx = i + 1
            end_idx = min(i + self.group_size, len(individual_pdfs))
            
            combined_writer = PdfWriter()
            
            # Title page for combined PDF
            if self.add_title_pages:
                title = f"Sections {start_idx}-{end_idx}"
                title_pdf = create_title_page(title, "Combined Document", page_size=self.page_size)
                title_reader = PdfReader(BytesIO(title_pdf))
                combined_writer.add_page(title_reader.pages[0])
            
            # Add each PDF
            for pdf_path in group:
                reader = PdfReader(str(pdf_path))
                for page in reader.pages:
                    combined_writer.add_page(page)
                self.log(f"  Added: {pdf_path.name}")
            
            # Save
            output_path = self.combined_dir / f"Combined_{start_idx:02d}-{end_idx:02d}.pdf"
            with open(output_path, 'wb') as f:
                combined_writer.write(f)
            
            self.log(f"Created: {output_path.name} ({len(combined_writer.pages)} pages)")
    
    def handle_set_aside_files(self):
        """Copy set-aside files to separate directory."""
        if not self.set_aside_files:
            return
        
        self.log(f"\n{'='*60}")
        self.log("Files set aside:")
        self.log('='*60)
        
        for file_path, reason in self.set_aside_files:
            try:
                dest = self.set_aside_dir / file_path.name
                # Handle duplicates
                counter = 1
                while dest.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    dest = self.set_aside_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.copy2(str(file_path), str(dest))
                self.log(f"  - {file_path.name}: {reason}")
            except Exception as e:
                self.log(f"  - {file_path.name}: Could not copy ({e})")
    
    def save_log(self):
        """Save processing log to file."""
        log_path = self.output_dir / "processing_log.txt"
        with open(log_path, 'w') as f:
            f.write('\n'.join(self.processing_log))
    
    def run(self) -> dict:
        """
        Run the full organization process.
        
        Returns:
            Summary dictionary with results
        """
        self.log('='*60)
        self.log("DocMerge - Document Organization Tool")
        self.log('='*60)
        self.log(f"Source: {self.source_dir}")
        self.log(f"Output: {self.output_dir}")
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.individual_dir.mkdir(exist_ok=True)
        self.combined_dir.mkdir(exist_ok=True)
        self.set_aside_dir.mkdir(exist_ok=True)
        
        # Discover and process categories
        categories = self.discover_categories()
        self.log(f"\nFound {len(categories)} categories")
        
        individual_pdfs = []
        for idx, (name, path) in enumerate(categories, 1):
            pdf_path = self.process_category(name, path, idx)
            if pdf_path:
                individual_pdfs.append(pdf_path)
        
        # Create combined PDFs
        if len(individual_pdfs) > 1:
            self.create_combined_pdfs(individual_pdfs)
        
        # Handle set-aside files
        self.handle_set_aside_files()
        
        # Save log
        self.save_log()
        
        # Summary
        self.log(f"\n{'='*60}")
        self.log("COMPLETE!")
        self.log(f"Output directory: {self.output_dir}")
        self.log(f"Individual PDFs: {len(individual_pdfs)}")
        self.log(f"Combined PDFs: {max(0, (len(individual_pdfs) + self.group_size - 1) // self.group_size) if self.group_size > 0 else 0}")
        self.log(f"Set aside files: {len(self.set_aside_files)}")
        self.log('='*60)
        
        return {
            'individual_pdfs': len(individual_pdfs),
            'combined_pdfs': max(0, (len(individual_pdfs) + self.group_size - 1) // self.group_size) if self.group_size > 0 else 0,
            'set_aside_files': len(self.set_aside_files),
            'output_dir': str(self.output_dir)
        }
