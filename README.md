# DocMerge 📄

A powerful command-line tool to organize and merge scattered documents (PDF, DOCX, images) into well-structured, categorized PDF files. Perfect for organizing course materials, project documentation, research papers, or any document collection.

## Features

- **Multi-format support**: PDF, DOCX, JPG, PNG, GIF, WEBP, JFIF, BMP, TIFF, HEIC
- **Smart organization**: Automatically discovers categories from folder structure
- **Intelligent sorting**: Files sorted by number prefix (1), 2), 3)...) then alphabetically
- **Combined PDFs**: Group multiple categories into merged PDFs
- **Title pages**: Auto-generated title pages for easy navigation
- **Image handling**: Auto-rotation based on EXIF, source labels added
- **DOCX conversion**: Text and tables extracted and formatted
- **Clean output**: System files automatically set aside

## Installation

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/gigwebs/docmerge.git
cd docmerge

# Install with pip
pip install -e .
```

### Manual Install

```bash
pip install pypdf pillow python-docx reportlab
```

Then add the docmerge directory to your PATH or create an alias.

## Usage

### Basic Usage

```bash
# Organize documents in a folder
docmerge /path/to/your/documents

# Specify custom output directory
docmerge /path/to/documents -o /path/to/output
```

### Options

| Option             | Description                                      |
| ------------------ | ------------------------------------------------ |
| `-o, --output`     | Output directory (default: `<source>_Organized`) |
| `-g, --group-size` | Categories per combined PDF (default: 3)         |
| `--no-combine`     | Skip creating combined PDFs                      |
| `--no-titles`      | Skip title pages                                 |
| `--no-labels`      | Skip source labels on images                     |
| `-p, --page-size`  | Page size: `a4` or `letter` (default: a4)        |
| `-q, --quiet`      | Minimal output                                   |
| `-v, --version`    | Show version                                     |

### Examples

```bash
# Organize course materials with 4 lectures per combined PDF
docmerge ~/Downloads/Course_Materials --group-size 4

# Create only individual PDFs (no combined)
docmerge ~/Documents/Project --no-combine

# Use Letter size for US standard
docmerge ~/Documents/Papers --page-size letter

# Quick processing with minimal output
docmerge ~/Downloads/Docs -q
```

## How It Works

1. **Discovery**: Scans source directory for subdirectories (each becomes a category)
2. **Sorting**: Files within each category sorted by leading numbers, then alphabetically
3. **Conversion**: Non-PDF files converted to PDF (images, DOCX)
4. **Individual PDFs**: Creates one PDF per category with title page
5. **Combined PDFs**: Groups categories into merged PDFs (e.g., 3 per file)
6. **Set Aside**: System files and unsupported formats moved to separate folder

## Output Structure

```
YourFolder_Organized/
├── Individual/
│   ├── 01_Category_Name.pdf
│   ├── 02_Another_Category.pdf
│   └── ...
├── Combined/
│   ├── Combined_01-03.pdf
│   ├── Combined_04-06.pdf
│   └── ...
├── Set_Aside/
│   └── (system files, unsupported formats)
└── processing_log.txt
```

## Terminal Shortcut (macOS/Linux)

Add this to your `~/.zshrc` or `~/.bashrc` for quick access:

```bash
# DocMerge shortcut
alias dm='docmerge'

# Or a function for common use case
merge-docs() {
    docmerge "$1" -o "${2:-${1}_Organized}"
}
```

Then use:

```bash
dm ~/Downloads/MyDocs
# or
merge-docs ~/Downloads/MyDocs ~/Desktop/Output
```

## Supported File Types

| Type   | Extensions                                                                  |
| ------ | --------------------------------------------------------------------------- |
| PDF    | `.pdf`                                                                      |
| Word   | `.docx`                                                                     |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.jfif`, `.bmp`, `.tiff`, `.heic` |

## Requirements

- Python 3.10+
- pypdf
- Pillow
- python-docx
- reportlab

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
