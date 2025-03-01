#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
import glob
from collections import defaultdict

def extract_text_from_tiptap(tiptap_content, resource_map=None):
    """
    Extract text from TipTap JSON structure.
    Handles resource references by converting them to USFM key term references.
    
    Args:
        tiptap_content: The TipTap content to process
        resource_map: A dictionary mapping resourceId to term names
    """
    # Handle the case where tiptap_content is a dictionary with 'type' and 'content' keys
    if isinstance(tiptap_content, dict):
        # If it's a text node
        if 'text' in tiptap_content:
            text = tiptap_content['text']
            
            # Check if it has resource reference marks
            if 'marks' in tiptap_content:
                for mark in tiptap_content.get('marks', []):
                    if mark.get('type') == 'resourceReference':
                        resource_id = mark.get('attrs', {}).get('resourceId')
                        if resource_map and resource_id in resource_map:
                            # Format as a USFM key term reference
                            return f"\\k {text}\\k*"
            
            # Regular text node without marks
            return text
        
        # If it has child content
        if 'content' in tiptap_content:
            result = ""
            for item in tiptap_content['content']:
                result += extract_text_from_tiptap(item, resource_map)
            return result
    
    # Handle the case where tiptap_content is a list of nodes
    elif isinstance(tiptap_content, list):
        result = ""
        for item in tiptap_content:
            result += extract_text_from_tiptap(item, resource_map)
        return result
    
    return ""

def format_scripture_references(text):
    """
    Find and format Scripture references in the text.
    
    Args:
        text: The text to process
    
    Returns:
        Text with Scripture references formatted as USFM cross-references
    """
    # List of Bible book names
    bible_books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
        "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
        "Psalm", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Song of Songs",
        "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
        "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
        "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
        "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians",
        "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy",
        "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John",
        "3 John", "Jude", "Revelation"
    ]
    
    # Process specific cases manually
    text = text.replace("Exodus 3:14", "\\xt Exodus 3:14\\xt*")
    text = text.replace("Luke 8:31", "\\xt Luke 8:31\\xt*")
    text = text.replace("Psalm 95", "\\xt Psalm 95\\xt*")
    text = text.replace("Acts 25-26", "\\xt Acts 25-26\\xt*")
    text = text.replace("Judges 5", "\\xt Judges 5\\xt*")
    text = text.replace("Zechariah 8", "\\xt Zechariah 8\\xt*")
    text = text.replace("Exodus 34:6", "\\xt Exodus 34:6\\xt*")
    
    # Handle "Genesis chapter 2" format
    for book in bible_books:
        pattern = f"{book} chapter (\\d+)"
        text = re.sub(pattern, f"\\\\xt {book} \\1\\\\xt*", text)
    
    # Handle "Hebrews chapters 3 and 4" format
    for book in bible_books:
        pattern = f"{book} chapters (\\d+) and (\\d+)"
        text = re.sub(pattern, f"\\\\xt {book} \\1-\\2\\\\xt*", text)
    
    # Handle "book of Judges" format
    for book in bible_books:
        pattern = f"book of {book}"
        text = re.sub(pattern, f"book of \\\\xt {book}\\\\xt*", text)
    
    return text

def build_resource_map(json_dir):
    """
    Build a mapping of resourceId to term names.
    """
    resource_map = {}
    json_files = glob.glob(os.path.join(json_dir, "*.json"))
    
    print(f"Found {len(json_files)} JSON files for resource map")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                resource_id = str(data.get('referenceId', ''))
                term_name = data.get('name', '')
                if resource_id and term_name:
                    resource_map[resource_id] = term_name
        except Exception as e:
            print(f"Error processing {json_file} for resource map: {e}")
    
    return resource_map

def extract_book_and_reference(filename):
    """
    Extract book name and reference from the filename.
    
    Args:
        filename: The filename to process (e.g., 'Matthew_7_1_12_132540.json')
    
    Returns:
        Tuple of (book_name, reference)
    """
    # Remove the ID and file extension
    base_name = os.path.basename(filename)
    parts = base_name.split('_')
    
    # Handle books with numbers (e.g., 1_Corinthians)
    if parts[0].isdigit():
        book_name = f"{parts[0]} {parts[1]}"
        reference_parts = parts[2:-1]  # Skip the ID at the end
    else:
        book_name = parts[0]
        reference_parts = parts[1:-1]  # Skip the ID at the end
    
    # Reconstruct the reference
    reference = "_".join(reference_parts)
    reference = reference.replace('_', ':')
    
    return book_name, reference

def get_book_id(book_name):
    """
    Get the USFM book ID for a given book name.
    
    Args:
        book_name: The name of the book
    
    Returns:
        The USFM book ID
    """
    book_ids = {
        "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM", "Deuteronomy": "DEU",
        "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT", "1 Samuel": "1SA", "2 Samuel": "2SA",
        "1 Kings": "1KI", "2 Kings": "2KI", "1 Chronicles": "1CH", "2 Chronicles": "2CH",
        "Ezra": "EZR", "Nehemiah": "NEH", "Esther": "EST", "Job": "JOB", "Psalms": "PSA",
        "Proverbs": "PRO", "Ecclesiastes": "ECC", "Song of Solomon": "SNG", "Isaiah": "ISA",
        "Jeremiah": "JER", "Lamentations": "LAM", "Ezekiel": "EZK", "Daniel": "DAN",
        "Hosea": "HOS", "Joel": "JOL", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON",
        "Micah": "MIC", "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP", "Haggai": "HAG",
        "Zechariah": "ZEC", "Malachi": "MAL", "Matthew": "MAT", "Mark": "MRK", "Luke": "LUK",
        "John": "JHN", "Acts": "ACT", "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO",
        "Galatians": "GAL", "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL",
        "1 Thessalonians": "1TH", "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI",
        "Titus": "TIT", "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE",
        "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN", "3 John": "3JN", "Jude": "JUD",
        "Revelation": "REV"
    }
    
    return book_ids.get(book_name, "UNK")

def process_json_file(file_path, resource_map):
    """
    Process a single JSON file and return the study note in USFM format.
    
    Args:
        file_path: Path to the JSON file
        resource_map: Dictionary mapping resourceId to term names
    
    Returns:
        Tuple of (book_name, reference, usfm_content)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract the reference
    reference = data.get('name', '')
    
    # Extract book name and reference from filename
    book_name, _ = extract_book_and_reference(file_path)
    
    # Extract content from TipTap format
    content_text = ""
    for content_item in data.get('content', []):
        if 'tiptap' in content_item:
            tiptap_data = content_item['tiptap']
            content_text += extract_text_from_tiptap(tiptap_data, resource_map)
    
    # Format Scripture references
    content_text = format_scripture_references(content_text)
    
    # Format as USFM study note
    usfm_content = f"\\im \\bd {reference}\\bd* {content_text}\n"
    
    return book_name, reference, usfm_content

def main():
    # Define input and output paths
    input_dir = "./json BiblicaStudyNotes/json/"
    output_dir = "./usfm_study_notes/"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Build resource map from key terms
    print("Building resource map from key terms...")
    resource_map = build_resource_map("./json BiblicaStudyNotesKeyTerms/json/")
    print(f"Found {len(resource_map)} key term resources")
    
    # Get all JSON files in the input directory
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    print(f"Found {len(json_files)} study note JSON files to process")
    
    # Group study notes by book
    book_notes = defaultdict(list)
    
    # Process each JSON file
    for i, json_file in enumerate(sorted(json_files)):
        try:
            if i % 10 == 0:
                print(f"Processing file {i+1}/{len(json_files)}")
            
            book_name, reference, usfm_content = process_json_file(json_file, resource_map)
            book_notes[book_name].append((reference, usfm_content))
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Create USFM files for each book
    for book_name, notes in book_notes.items():
        book_id = get_book_id(book_name)
        output_file = os.path.join(output_dir, f"{book_id}_StudyNotes.SFM")
        
        # Sort notes by reference
        notes.sort()
        
        # Create USFM header with license information
        usfm_content = f"""\\id {book_id} - Biblica Study Notes
\\rem Copyright © 2023 by Biblica, Inc.
\\h {book_name} Study Notes
\\toc1 {book_name} Study Notes
\\toc2 {book_name} Study Notes
\\toc3 {book_name}
\\mt1 {book_name} Study Notes

\\periph Copyright Information
\\mt Biblica Study Notes
\\pc Copyright © 2023 Biblica, Inc.
\\pc https://www.biblica.com/
\\pc Licensed under CC BY-SA 4.0 license
\\pc https://creativecommons.org/licenses/by-sa/4.0/legalcode.en

"""
        
        # Add all notes for this book
        for _, note_content in notes:
            usfm_content += note_content
        
        # Write the USFM content to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(usfm_content)
        
        print(f"Created {output_file} with {len(notes)} study notes")
    
    print(f"Conversion complete. Output written to {output_dir}")

if __name__ == "__main__":
    main() 