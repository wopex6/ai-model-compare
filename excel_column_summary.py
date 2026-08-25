#!/usr/bin/env python3
"""
Read a column from an Excel file and provide a summary of all text in it.
"""

import pandas as pd
import sys
from collections import Counter
import re

def clean_text(text):
    """Extract words from text and clean them"""
    if pd.isna(text) or text is None:
        return ""
    # Convert to string and extract alphanumeric words
    text = str(text)
    words = re.findall(r'\b\w+\b', text.lower())
    return ' '.join(words)

def summarize_column(file_path, column_name=None, column_index=None):
    """
    Read a column from Excel file and provide summary
    
    Args:
        file_path: Path to Excel file
        column_name: Name of the column to read (takes precedence over column_index)
        column_index: Index of the column (0-based) if column_name not provided
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Determine which column to use
        if column_name and column_name in df.columns:
            column_data = df[column_name]
            print(f"Reading column: '{column_name}'")
        elif column_index is not None and column_index < len(df.columns):
            column_data = df.iloc[:, column_index]
            print(f"Reading column index {column_index}: '{df.columns[column_index]}'")
        else:
            available_columns = list(df.columns)
            print("Available columns:")
            for i, col in enumerate(available_columns):
                print(f"  {i}: {col}")
            raise ValueError("Column not found. Please specify a valid column name or index.")
        
        # Remove empty values
        non_empty_data = column_data.dropna()
        non_empty_data = non_empty_data[non_empty_data.astype(str).str.strip() != '']
        
        if len(non_empty_data) == 0:
            print("No non-empty data found in the column.")
            return
        
        # Basic statistics
        print(f"\n=== COLUMN SUMMARY ===")
        print(f"Total rows: {len(column_data)}")
        print(f"Non-empty rows: {len(non_empty_data)}")
        print(f"Empty rows: {len(column_data) - len(non_empty_data)}")
        
        # Combine all text
        all_text = ' '.join([str(val) for val in non_empty_data])
        clean_all_text = clean_text(all_text)
        
        # Word analysis
        words = clean_all_text.split()
        word_count = len(words)
        unique_words = len(set(words))
        
        print(f"\nTotal words: {word_count}")
        print(f"Unique words: {unique_words}")
        print(f"Average words per cell: {word_count / len(non_empty_data):.2f}")
        
        # Most common words
        if words:
            word_freq = Counter(words)
            print(f"\nTop 10 most common words:")
            for word, count in word_freq.most_common(10):
                print(f"  {word}: {count}")
        
        # Text length analysis
        text_lengths = [len(str(val)) for val in non_empty_data]
        if text_lengths:
            print(f"\nText length statistics:")
            print(f"  Min length: {min(text_lengths)} characters")
            print(f"  Max length: {max(text_lengths)} characters")
            print(f"  Average length: {sum(text_lengths) / len(text_lengths):.2f} characters")
        
        # Sample of unique values
        unique_values = non_empty_data.unique()
        print(f"\nUnique values count: {len(unique_values)}")
        if len(unique_values) <= 10:
            print("All unique values:")
            for val in unique_values:
                print(f"  - {val}")
        else:
            print("Sample of unique values:")
            for val in unique_values[:10]:
                print(f"  - {val}")
            print(f"  ... and {len(unique_values) - 10} more")
        
        # Full text summary
        print(f"\n=== FULL TEXT CONTENT ===")
        print("Combined text from all non-empty cells:")
        print("-" * 50)
        print(all_text[:1000])  # Show first 1000 characters
        if len(all_text) > 1000:
            print(f"... (truncated, total length: {len(all_text)} characters)")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nUsage examples:")
        print("python excel_column_summary.py file.xlsx --column 'Column Name'")
        print("python excel_column_summary.py file.xlsx --index 0")

def main():
    if len(sys.argv) < 2:
        print("Usage: python excel_column_summary.py <excel_file> [--column 'Column Name' | --index 0]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    column_name = None
    column_index = None
    
    # Parse command line arguments
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == '--column' and i + 1 < len(sys.argv):
            column_name = sys.argv[i + 1]
        elif sys.argv[i] == '--index' and i + 1 < len(sys.argv):
            try:
                column_index = int(sys.argv[i + 1])
            except ValueError:
                print("Error: Column index must be a number")
                sys.exit(1)
    
    summarize_column(file_path, column_name, column_index)

if __name__ == "__main__":
    main()
