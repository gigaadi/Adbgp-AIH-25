# PDF to JSON Outline Converter

A Python tool that extracts the outline/bookmarks from a PDF file and converts them to JSON format.

## Features

- Extracts PDF outlines/bookmarks recursively
- Converts to structured JSON format
- Handles nested outline items
- Preserves outline hierarchy levels
- Includes page numbers and formatting information
- Command-line interface for easy use

## Installation

1. Clone or download this project
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Usage

```bash
python pdf_to_json_converter.py <pdf_file_path>
```

### Example

```bash
python pdf_to_json_converter.py document.pdf
```

This will create a JSON file named `document_outline.json` in the same directory.

### Programmatic Usage

```python
from pdf_to_json_converter import PDFOutlineConverter

# Create converter instance
converter = PDFOutlineConverter("document.pdf")

# Convert to JSON
output_file = converter.convert_to_json()

# Or specify custom output path
output_file = converter.convert_to_json("custom_output.json")
```

## Output Format

The JSON output contains:

```json
{
  "pdf_filename": "document.pdf",
  "total_outline_items": 5,
  "outline": [
    {
      "title": "Chapter 1",
      "level": 0,
      "page_number": 1,
      "children": [],
      "bold": true,
      "italic": false
    },
    {
      "title": "Section 1.1",
      "level": 1,
      "page_number": 3,
      "children": []
    }
  ]
}
```

### Output Fields

- **pdf_filename**: Name of the input PDF file
- **total_outline_items**: Total number of outline items extracted
- **outline**: Array of outline items, each containing:
  - **title**: The outline item title/text
  - **level**: Nesting level (0 = top level, 1 = first sublevel, etc.)
  - **page_number**: Page number where the item appears (1-indexed)
  - **children**: Array for nested items (currently empty, structure preserved for future use)
  - **bold**: Whether the item is bold (if available)
  - **italic**: Whether the item is italic (if available)
  - **color**: Color information (if available)

## Requirements

- Python 3.6 or higher
- PyPDF2 library

## Error Handling

The tool handles various error scenarios:

- Missing PDF files
- PDFs without outlines/bookmarks
- Corrupted PDF files
- Permission issues

## Limitations

- Only extracts existing outlines/bookmarks from PDFs
- Cannot generate outlines from PDFs that don't have them
- Page numbers may not be available for all outline items
- Some PDF formatting information might not be preserved

## Troubleshooting

### "No outline/bookmarks found"
This means the PDF doesn't have a built-in outline or bookmarks. The tool cannot generate outlines from PDF content.

### "File not found"
Make sure the PDF file path is correct and the file exists.

### "Error reading PDF"
The PDF might be corrupted or password-protected. Try opening it in a PDF reader first.

## License

This project is created for the Adobe India Hackathon Round 1A. 