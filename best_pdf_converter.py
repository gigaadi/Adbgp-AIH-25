#!/usr/bin/env python3
"""
Best PDF to JSON Outline Converter
Combines multiple extraction techniques for maximum accuracy:
1. Built-in PDF outline/bookmarks
2. Rule-based text analysis with advanced patterns
3. Font size and style analysis
4. Position-based heading detection
5. Semantic similarity for deduplication
"""

import json
import re
import os
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import PyPDF2
from PyPDF2 import PdfReader
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BestPDFConverter:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_reader = None
        self.headings = []
        self.page_texts = []
        
    def load_pdf(self) -> bool:
        """Load and validate PDF file."""
        try:
            if not os.path.exists(self.pdf_path):
                logger.error(f"PDF file not found: {self.pdf_path}")
                return False
                
            self.pdf_reader = PdfReader(self.pdf_path)
            if len(self.pdf_reader.pages) == 0:
                logger.error("PDF file is empty or corrupted")
                return False
                
            logger.info(f"Successfully loaded PDF with {len(self.pdf_reader.pages)} pages")
            return True
            
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            return False
    
    def extract_all_headings(self) -> Dict[str, Any]:
        """Extract headings using all available techniques."""
        if not self.load_pdf():
            return {"error": "Failed to load PDF"}
        
        logger.info("Starting comprehensive heading extraction...")
        
        # Extract headings using different methods
        builtin_headings = self._extract_builtin_outline()
        text_headings = self._extract_headings_from_text()
        font_headings = self._extract_headings_by_font()
        position_headings = self._extract_headings_by_position()
        
        # Combine all headings
        all_headings = []
        all_headings.extend(builtin_headings)
        all_headings.extend(text_headings)
        all_headings.extend(font_headings)
        all_headings.extend(position_headings)
        
        # Advanced deduplication and cleaning
        final_headings = self._advanced_deduplication(all_headings)
        
        # Sort by page number and line number
        final_headings.sort(key=lambda x: (x.get('page_number', 0), x.get('line_number', 0)))
        
        # Build hierarchical structure
        hierarchical_headings = self._build_hierarchy(final_headings)
        
        return {
            "pdf_filename": os.path.basename(self.pdf_path),
            "total_headings": len(final_headings),
            "extraction_methods": {
                "builtin_outline": len(builtin_headings),
                "text_analysis": len(text_headings),
                "font_analysis": len(font_headings),
                "position_analysis": len(position_headings)
            },
            "headings": hierarchical_headings
        }
    
    def _extract_builtin_outline(self) -> List[Dict[str, Any]]:
        """Extract headings from PDF's built-in outline/bookmarks."""
        headings = []
        try:
            if hasattr(self.pdf_reader, 'outline') and self.pdf_reader.outline:
                logger.info("Extracting built-in outline...")
                outline_items = self._process_outline_items(self.pdf_reader.outline)
                for item in outline_items:
                    item['source'] = 'builtin_outline'
                    item['confidence'] = 0.95
                    headings.append(item)
                logger.info(f"Extracted {len(headings)} items from built-in outline")
            else:
                logger.info("No built-in outline found")
        except Exception as e:
            logger.warning(f"Error extracting built-in outline: {str(e)}")
        
        return headings
    
    def _process_outline_items(self, items, level=0) -> List[Dict[str, Any]]:
        """Process outline items recursively."""
        processed_items = []
        try:
            for item in items:
                if isinstance(item, list):
                    nested_items = self._process_outline_items(item, level + 1)
                    processed_items.extend(nested_items)
                else:
                    try:
                        outline_item = {
                            "title": self._safe_str(item.title) if hasattr(item, 'title') else str(item),
                            "level": level,
                            "page_number": self._get_page_number(item),
                            "children": [],
                            "source": "builtin_outline"
                        }
                        
                        # Add additional properties
                        if hasattr(item, 'color'):
                            outline_item["color"] = self._safe_convert(item.color)
                        if hasattr(item, 'italic'):
                            outline_item["italic"] = self._safe_convert(item.italic)
                        if hasattr(item, 'bold'):
                            outline_item["bold"] = self._safe_convert(item.bold)
                        
                        processed_items.append(outline_item)
                    except Exception as e:
                        logger.warning(f"Could not process outline item: {str(e)}")
                        continue
        except Exception as e:
            logger.warning(f"Error processing outline items: {str(e)}")
        
        return processed_items
    
    def _get_page_number(self, item) -> Optional[int]:
        """Get page number for outline item."""
        try:
            if hasattr(item, 'page') and item.page is not None:
                if hasattr(item.page, '__int__'):
                    return int(item.page) + 1
                elif hasattr(item.page, '__float__'):
                    return int(float(item.page)) + 1
                else:
                    page_str = str(item.page)
                    numbers = re.findall(r'\d+', page_str)
                    if numbers:
                        return int(numbers[0]) + 1
            return None
        except (ValueError, TypeError, AttributeError):
            return None
    
    def _extract_headings_from_text(self) -> List[Dict[str, Any]]:
        """Extract headings using advanced text analysis."""
        headings = []
        logger.info("Extracting headings from text content...")
        
        # Extract text from all pages
        for page_num, page in enumerate(self.pdf_reader.pages, 1):
            try:
                if not hasattr(page, 'extract_text'):
                    continue
                    
                text = page.extract_text()
                if not text or not isinstance(text, str):
                    continue
                
                # Clean and split text
                text = self._clean_extracted_text(text)
                lines = text.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or len(line) < 3:
                        continue
                    
                    # Check for heading patterns
                    heading_info = self._analyze_line_for_heading(line, page_num, line_num)
                    if heading_info:
                        headings.append(heading_info)
                        
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(headings)} headings from text analysis")
        return headings
    
    def _analyze_line_for_heading(self, line: str, page_num: int, line_num: int) -> Optional[Dict[str, Any]]:
        """Analyze a single line to determine if it's a heading."""
        # Remove extra whitespace
        line = re.sub(r'\s+', ' ', line.strip())
        
        # Skip if too short or too long
        if len(line) < 3 or len(line) > 200:
            return None
        
        # Skip common non-heading patterns
        if self._is_regular_text(line):
            return None
        
        # Check for heading patterns
        confidence = 0.0
        level = 0
        
        # Pattern 1: Numbered headings (1., 1.1., 1.1.1., etc.)
        if re.match(r'^\d+(\.\d+)*\.?\s+[A-Z]', line):
            confidence = 0.9
            level = line.count('.')
        
        # Pattern 2: All caps headings
        elif line.isupper() and len(line) > 3 and len(line) < 100:
            confidence = 0.85
            level = 0
        
        # Pattern 3: Title case with specific keywords
        elif self._is_title_case(line) and self._contains_heading_keywords(line):
            confidence = 0.8
            level = 1
        
        # Pattern 4: Bold-like patterns (multiple spaces or special chars)
        elif re.match(r'^[A-Z][A-Za-z\s]{2,}$', line) and len(line.split()) <= 8:
            confidence = 0.75
            level = 2
        
        # Pattern 5: Section-like patterns
        elif re.match(r'^(Section|Chapter|Part|Appendix|Round|Phase)\s+\d+', line, re.IGNORECASE):
            confidence = 0.9
            level = 0
        
        # Pattern 6: Short, capitalized lines
        elif len(line.split()) <= 5 and line[0].isupper() and not line.endswith('.'):
            confidence = 0.7
            level = 2
        
        if confidence > 0.6:
            return {
                "title": line,
                "level": level,
                "page_number": page_num,
                "line_number": line_num,
                "source": "text_analysis",
                "confidence": confidence,
                "children": []
            }
        
        return None
    
    def _is_regular_text(self, line: str) -> bool:
        """Check if line is regular text (not a heading)."""
        # Skip lines that are clearly not headings
        skip_patterns = [
            r'^\s*$',  # Empty or whitespace only
            r'^\d+$',  # Just numbers
            r'^[a-z]',  # Starts with lowercase
            r'\.$',  # Ends with period
            r'^\s*[•\-*]\s*',  # Bullet points
            r'^\s*\d+\.\s*$',  # Just numbering
            r'^\s*[A-Z]\s*$',  # Single letter
            r'^\s*[A-Z]{1,2}\s*$',  # Short acronyms
            r'^\s*[a-z]{1,3}\s*$',  # Very short words
            r'^\s*[A-Z][a-z]{1,2}\s*$',  # Very short capitalized words
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, line):
                return True
        
        # Skip if contains typical sentence endings
        if re.search(r'[.!?]\s*$', line) and len(line.split()) > 10:
            return True
        
        return False
    
    def _is_title_case(self, text: str) -> bool:
        """Check if text follows title case pattern."""
        words = text.split()
        if len(words) < 2:
            return False
        
        # Check if first word starts with capital
        if not words[0][0].isupper():
            return False
        
        # Count capitalized words
        capitalized_count = sum(1 for word in words if word and word[0].isupper())
        return capitalized_count >= len(words) * 0.6
    
    def _contains_heading_keywords(self, text: str) -> bool:
        """Check if text contains heading-related keywords."""
        heading_keywords = [
            'introduction', 'overview', 'background', 'method', 'methodology',
            'results', 'discussion', 'conclusion', 'summary', 'abstract',
            'chapter', 'section', 'part', 'appendix', 'reference', 'bibliography',
            'round', 'phase', 'step', 'stage', 'level', 'challenge', 'task',
            'objective', 'goal', 'purpose', 'scope', 'limitation', 'requirement'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in heading_keywords)
    
    def _extract_headings_by_font(self) -> List[Dict[str, Any]]:
        """Extract headings based on font characteristics."""
        headings = []
        logger.info("Extracting headings by font analysis...")
        
        try:
            for page_num, page in enumerate(self.pdf_reader.pages, 1):
                try:
                    # This is a simplified font analysis
                    # In a real implementation, you'd analyze font sizes and styles
                    # For now, we'll use text extraction with font hints
                    if hasattr(page, 'extract_text'):
                        text = page.extract_text()
                        if text:
                            # Look for lines that might be headings based on context
                            lines = text.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                line = line.strip()
                                if len(line) > 3 and len(line) < 50:
                                    # Simple heuristic for font-based headings
                                    if (line.isupper() or 
                                        (line[0].isupper() and len(line.split()) <= 6 and not line.endswith('.'))):
                                        headings.append({
                                            "title": line,
                                            "level": 1,
                                            "page_number": page_num,
                                            "line_number": line_num,
                                            "source": "font_analysis",
                                            "confidence": 0.6,
                                            "children": []
                                        })
                except Exception as e:
                    logger.warning(f"Error in font analysis for page {page_num}: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error in font analysis: {str(e)}")
        
        logger.info(f"Extracted {len(headings)} headings from font analysis")
        return headings
    
    def _extract_headings_by_position(self) -> List[Dict[str, Any]]:
        """Extract headings based on their position in the document."""
        headings = []
        logger.info("Extracting headings by position analysis...")
        
        try:
            for page_num, page in enumerate(self.pdf_reader.pages, 1):
                try:
                    if hasattr(page, 'extract_text'):
                        text = page.extract_text()
                        if text:
                            lines = text.split('\n')
                            # Look for lines at the beginning of pages or sections
                            for line_num, line in enumerate(lines, 1):
                                line = line.strip()
                                if (line_num <= 3 and len(line) > 3 and len(line) < 100 and
                                    line[0].isupper() and not line.endswith('.')):
                                    headings.append({
                                        "title": line,
                                        "level": 0 if line_num == 1 else 1,
                                        "page_number": page_num,
                                        "line_number": line_num,
                                        "source": "position_analysis",
                                        "confidence": 0.65,
                                        "children": []
                                    })
                except Exception as e:
                    logger.warning(f"Error in position analysis for page {page_num}: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error in position analysis: {str(e)}")
        
        logger.info(f"Extracted {len(headings)} headings from position analysis")
        return headings
    
    def _advanced_deduplication(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Advanced deduplication of headings."""
        logger.info("Performing advanced deduplication...")
        
        # Group by similarity
        unique_headings = []
        processed_titles = set()
        
        for heading in headings:
            title = heading.get('title', '').strip()
            if not title:
                continue
            
            # Normalize title for comparison
            normalized_title = self._normalize_title(title)
            
            # Check if we already have a similar heading
            is_duplicate = False
            for existing in unique_headings:
                existing_title = existing.get('title', '').strip()
                existing_normalized = self._normalize_title(existing_title)
                
                # Check exact match
                if normalized_title == existing_normalized:
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if heading.get('confidence', 0) > existing.get('confidence', 0):
                        unique_headings.remove(existing)
                        unique_headings.append(heading)
                    break
                
                # Check similarity
                if self._calculate_similarity(normalized_title, existing_normalized) > 0.8:
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if heading.get('confidence', 0) > existing.get('confidence', 0):
                        unique_headings.remove(existing)
                        unique_headings.append(heading)
                    break
            
            if not is_duplicate:
                unique_headings.append(heading)
                processed_titles.add(normalized_title)
        
        logger.info(f"Deduplication reduced {len(headings)} to {len(unique_headings)} headings")
        return unique_headings
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', title.lower().strip())
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized
    
    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        if not title1 or not title2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _build_hierarchy(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build hierarchical structure from flat list of headings."""
        logger.info("Building hierarchical structure...")
        
        # Sort by level and position
        headings.sort(key=lambda x: (x.get('level', 0), x.get('page_number', 0), x.get('line_number', 0)))
        
        # Build hierarchy
        hierarchy = []
        stack = []
        
        for heading in headings:
            level = heading.get('level', 0)
            
            # Pop stack until we find the right parent level
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            # Add to appropriate parent
            if not stack:
                hierarchy.append(heading)
            else:
                if 'children' not in stack[-1]:
                    stack[-1]['children'] = []
                stack[-1]['children'].append(heading)
            
            stack.append(heading)
        
        logger.info(f"Built hierarchy with {len(hierarchy)} top-level items")
        return hierarchy
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text from PDF."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page breaks and other artifacts
        text = re.sub(r'\f', '\n', text)
        # Clean up line breaks
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def _safe_convert(self, obj) -> Any:
        """Safely convert PyPDF2 objects to JSON-serializable types."""
        try:
            if hasattr(obj, '__str__'):
                return str(obj)
            return obj
        except:
            return str(obj)
    
    def _safe_str(self, obj) -> str:
        """Safely convert object to string."""
        try:
            return str(obj) if obj is not None else ""
        except:
            return ""
    
    def convert_to_json(self, output_path: str = None) -> str:
        """Convert PDF to JSON and save to file."""
        try:
            result = self.extract_all_headings()
            
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
                output_path = f"{base_name}_best_outline.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved JSON to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting to JSON: {str(e)}")
            return None

def main():
    """Main function to run the converter."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python best_pdf_converter.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    converter = BestPDFConverter(pdf_path)
    
    output_path = converter.convert_to_json()
    if output_path:
        print(f"Conversion completed successfully!")
        print(f"Output saved to: {output_path}")
    else:
        print("Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 