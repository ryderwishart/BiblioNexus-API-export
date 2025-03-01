#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
import glob

def extract_text_from_tiptap(tiptap_content, resource_map=None):
    """
    Extract plain text from TipTap JSON structure.
    Handles resource references by converting them to USFM cross-references.
    
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
                            # Format as a USFM cross-reference using \k tag
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

def process_json_file(file_path, resource_map):
    """
    Process a single JSON file and return a dictionary entry in USFM format.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract the key term name
    term_name = data.get('name', '')
    
    # Extract content from TipTap format
    content_text = ""
    for content_item in data.get('content', []):
        if 'tiptap' in content_item:
            tiptap_data = content_item['tiptap']
            content_text += extract_text_from_tiptap(tiptap_data, resource_map)
    
    # Format Scripture references
    content_text = format_scripture_references(content_text)
    
    # Format as USFM dictionary entry
    usfm_entry = f"\\p \\k {term_name}\\k*\\im {content_text}"
    
    return usfm_entry

def main():
    # Define input and output paths
    input_dir = "./json BiblicaStudyNotesKeyTerms/json/"
    output_file = "./BiblicaKeyTerms.sfm"
    
    # Build resource map
    print("Building resource map...")
    resource_map = build_resource_map(input_dir)
    print(f"Found {len(resource_map)} resources")
    
    # Get all JSON files in the input directory
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    print(f"Found {len(json_files)} JSON files to process")
    
    # Create USFM header with license information
    usfm_content = """\\id BD
\\c 1
\\ms Biblica Key Terms Dictionary

\\periph Copyright Information
\\mt Biblica Bible Dictionary
\\pc Copyright © 2023 Biblica, Inc.
\\pc https://www.biblica.com/
\\pc Licensed under CC BY-SA 4.0 license
\\pc https://creativecommons.org/licenses/by-sa/4.0/legalcode.en

"""
    
    # Process each JSON file
    for i, json_file in enumerate(sorted(json_files)):
        try:
            if i % 10 == 0:
                print(f"Processing file {i+1}/{len(json_files)}")
            entry = process_json_file(json_file, resource_map)
            usfm_content += entry + "\n"
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Write the USFM content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(usfm_content)
    
    print(f"Conversion complete. Output written to {output_file}")

if __name__ == "__main__":
    main() 