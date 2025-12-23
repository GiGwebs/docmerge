#!/usr/bin/env python3
"""
Command-line interface for DocMerge.
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .organizer import DocumentOrganizer


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='docmerge',
        description='Organize and merge documents into structured PDFs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage - organize a folder of documents
  docmerge /path/to/documents

  # Specify output directory
  docmerge /path/to/documents -o /path/to/output

  # Combine 4 sections per merged PDF instead of default 3
  docmerge /path/to/documents --group-size 4

  # Skip combined PDFs, only create individual section PDFs
  docmerge /path/to/documents --no-combine

  # Use Letter page size instead of A4
  docmerge /path/to/documents --page-size letter

  # Quiet mode (minimal output)
  docmerge /path/to/documents -q

Supported file formats:
  - PDF (.pdf)
  - Word documents (.docx)
  - Images (.jpg, .jpeg, .png, .gif, .webp, .jfif, .bmp, .tiff, .heic)

How it works:
  1. Scans the source directory for subdirectories (categories)
  2. Creates one PDF per category with all files merged
  3. Creates combined PDFs grouping multiple categories together
  4. Sets aside unsupported or system files
'''
    )

    parser.add_argument(
        'source',
        type=str,
        help='Source directory containing documents to organize'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output directory (default: <source>_Organized)'
    )

    parser.add_argument(
        '-g', '--group-size',
        type=int,
        default=3,
        help='Number of sections to combine per merged PDF (default: 3)'
    )

    parser.add_argument(
        '--no-combine',
        action='store_true',
        help='Skip creating combined PDFs'
    )

    parser.add_argument(
        '--no-titles',
        action='store_true',
        help='Skip adding title pages to PDFs'
    )

    parser.add_argument(
        '--no-labels',
        action='store_true',
        help='Skip adding source labels to converted images'
    )

    parser.add_argument(
        '-p', '--page-size',
        type=str,
        choices=['a4', 'A4', 'letter', 'LETTER'],
        default='A4',
        help='Page size for converted documents (default: A4)'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - minimal output'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    args = parser.parse_args()

    # Validate source directory
    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists():
        print(f"Error: Source directory does not exist: {source_path}")
        sys.exit(1)
    if not source_path.is_dir():
        print(f"Error: Source path is not a directory: {source_path}")
        sys.exit(1)

    # Set output directory
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = source_path.parent / f"{source_path.name}_Organized"

    # Run organizer
    organizer = DocumentOrganizer(
        source_dir=str(source_path),
        output_dir=str(output_path),
        group_size=0 if args.no_combine else args.group_size,
        page_size=args.page_size.upper(),
        add_title_pages=not args.no_titles,
        add_source_labels=not args.no_labels,
        verbose=not args.quiet
    )

    try:
        result = organizer.run()
        if not args.quiet:
            print(f"\nOutput saved to: {result['output_dir']}")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
