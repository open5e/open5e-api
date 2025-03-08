import json
import logging
from pathlib import Path
import re
from tabulate import tabulate

# Configure basic logging to show INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_markdown(content: str) -> str:
    """Clean markdown content."""
    if not content:
        return content
    
    # Normalize line endings
    content = content.replace('\r\n', '\n\n')
    content = content.replace('\n\n\n\n', '\n\n')
    
    # Find and clean tables
    def clean_table(match):
        # Split into lines and filter out empty ones
        lines = [line.strip() for line in match.group(0).split('\n') if line.strip()]
        if len(lines) < 3:  # Need at least header, separator, and one data row
            return match.group(0)
            
        # Parse the table
        headers = [cell.strip() for cell in lines[0].split('|')[1:-1]]
        rows = [[cell.strip() for cell in line.split('|')[1:-1]] for line in lines[2:]]
        
        # Rebuild table with tabulate
        return tabulate(rows, headers, tablefmt="pipe")
    
    # Find and process tables (matches from | header | to last row)
    table_pattern = r'\|[^\n]+\|[\n\s]*\|[-\s|]+\|[\n\s]*(?:\|[^\n]+\|[\n\s]*]*)+'
    content = re.sub(table_pattern, clean_table, content)
    
    return content

def clean_json_file(file_path: Path) -> None:
    """Clean markdown content in JSON fixture file."""
    # Skip if not in a v2 directory
    if '/v2/' not in str(file_path):
        return

    markdown_fields = ['desc', 'equipment', 'traits', 'languages_desc', 
                      'asi_desc', 'feature_desc', 'suggested_characteristics']

    try:
        data = json.loads(file_path.read_text(encoding='utf-8'))
        modified = False

        for item in data:
            if isinstance(item, dict) and 'fields' in item:
                fields = item['fields']
                for field in markdown_fields:
                    if field in fields and isinstance(fields[field], str):
                        cleaned = clean_markdown(fields[field])
                        if cleaned != fields[field]:
                            fields[field] = cleaned
                            modified = True

        if modified:
            file_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.info(f"Cleaned markdown in {file_path}")

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")

def clean_data_directory(directory: str) -> None:
    """Clean all JSON files in directory recursively."""
    json_files = Path(directory).rglob('*.json')
    for file_path in json_files:
        clean_json_file(file_path)