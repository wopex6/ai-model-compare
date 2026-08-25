#!/usr/bin/env python3
"""
Read a column from an Excel file and provide a contextual summary using AI.
"""

import pandas as pd
import sys
import json
from datetime import datetime
import os

def get_ai_summary(column_name, all_values, combined_text):
    """Use AI to provide contextual summary of the column content"""
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or not api_key.strip():
            return "AI summary not available: No OpenAI API key configured"
        
        client = OpenAI(api_key=api_key, timeout=30.0)
        
        # Prepare the prompt
        prompt = f"""You are analyzing a column named "{column_name}" from an Excel file. 

Here are all the non-empty values from this column:
{json.dumps(all_values, indent=2, ensure_ascii=False)}

Combined text from all cells:
{combined_text[:3000]}{"..." if len(combined_text) > 3000 else ""}

Please provide a comprehensive contextual summary that includes:

1. **Content Theme**: What is this column about? What type of information does it contain?
2. **Key Patterns**: What are the main patterns, categories, or themes you observe?
3. **Data Characteristics**: What format is the data in? Are there any notable characteristics?
4. **Business/Domain Context**: What domain or business context might this data belong to?
5. **Notable Insights**: Any interesting observations, outliers, or patterns worth noting?
6. **Data Quality**: Any issues with data quality, consistency, or completeness?

Provide your analysis in a clear, structured format with headings for each section."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analysis expert who provides insightful, contextual summaries of column data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"AI analysis failed: {str(e)}"

def get_fallback_summary(column_name, all_values, combined_text):
    """Provide a basic summary when AI is not available"""
    # Basic pattern detection
    patterns = {
        'Email addresses': bool(any('@' in str(v) and '.' in str(v) for v in all_values)),
        'Phone numbers': bool(any(re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', str(v)) for v in all_values)),
        'Dates': bool(any(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', str(v)) for v in all_values)),
        'Numbers only': all(str(v).replace('.', '').replace('-', '').isdigit() for v in all_values if pd.notna(v)),
        'URLs': bool(any('http' in str(v).lower() for v in all_values)),
        'Names/People': bool(any(len(str(v).split()) <= 4 and str(v).strip().istitle() for v in all_values if pd.notna(v) and len(str(v)) > 3)),
    }
    
    # Length analysis
    avg_length = sum(len(str(v)) for v in all_values) / len(all_values) if all_values else 0
    
    summary = f"""
=== CONTEXTUAL SUMMARY FOR COLUMN: {column_name} ===

**Content Theme:**
This column contains {len(all_values)} entries with an average length of {avg_length:.1f} characters.

**Observed Patterns:**
"""
    
    for pattern, exists in patterns.items():
        if exists:
            summary += f"- {pattern}\n"
    
    summary += f"""
**Data Characteristics:**
- Total entries: {len(all_values)}
- Unique entries: {len(set(all_values))}
- Most common value: "{max(set(all_values), key=all_values.count)}" ({all_values.count(max(set(all_values), key=all_values.count))} occurrences)

**Sample Content:**
{json.dumps(all_values[:10], indent=2, ensure_ascii=False)}
"""
    
    return summary

def analyze_column_context(file_path, column_name=None, column_index=None, use_ai=True):
    """
    Read a column from Excel file and provide contextual summary
    
    Args:
        file_path: Path to Excel file
        column_name: Name of the column to read (takes precedence over column_index)
        column_index: Index of the column (0-based) if column_name not provided
        use_ai: Whether to use AI for analysis (default: True)
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Determine which column to use
        if column_name and column_name in df.columns:
            column_data = df[column_name]
            col_name = column_name
            print(f"Analyzing column: '{column_name}'")
        elif column_index is not None and column_index < len(df.columns):
            column_data = df.iloc[:, column_index]
            col_name = df.columns[column_index]
            print(f"Analyzing column index {column_index}: '{col_name}'")
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
        
        # Prepare data for analysis
        all_values = [str(val) for val in non_empty_data]
        combined_text = ' '.join(all_values)
        
        print(f"\n{'='*60}")
        print(f"CONTEXTUAL ANALYSIS FOR COLUMN: {col_name}")
        print(f"{'='*60}")
        print(f"File: {file_path}")
        print(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total entries: {len(column_data)} | Non-empty: {len(non_empty_data)}")
        print(f"{'='*60}\n")
        
        # Get summary
        if use_ai:
            print("Generating AI-powered contextual summary...\n")
            summary = get_ai_summary(col_name, all_values, combined_text)
        else:
            print("Generating basic contextual summary...\n")
            summary = get_fallback_summary(col_name, all_values, combined_text)
        
        print(summary)
        
        # Additional insights
        print(f"\n{'='*60}")
        print("ADDITIONAL INSIGHTS")
        print(f"{'='*60}")
        
        # Data type analysis
        data_types = {}
        for val in all_values:
            dtype = "Numeric" if val.replace('.', '').replace('-', '').isdigit() else "Text"
            data_types[dtype] = data_types.get(dtype, 0) + 1
        
        print(f"Data types: {data_types}")
        
        # Length distribution
        lengths = [len(val) for val in all_values]
        print(f"Length range: {min(lengths)} - {max(lengths)} characters")
        print(f"Average length: {sum(lengths)/len(lengths):.1f} characters")
        
        # Consistency check
        unique_count = len(set(all_values))
        consistency = (unique_count / len(all_values)) * 100
        print(f"Data consistency: {consistency:.1f}% unique values")
        
        if consistency > 90:
            print("→ High uniqueness - likely free-text or identifiers")
        elif consistency > 50:
            print("→ Medium uniqueness - mixed categorical/text data")
        else:
            print("→ Low uniqueness - likely categorical/repeated values")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nUsage examples:")
        print("python excel_context_summary.py file.xlsx --column 'Column Name'")
        print("python excel_context_summary.py file.xlsx --index 0")
        print("python excel_context_summary.py file.xlsx --column 'Name' --no-ai")

def main():
    if len(sys.argv) < 2:
        print("Usage: python excel_context_summary.py <excel_file> [--column 'Column Name' | --index 0] [--no-ai]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    column_name = None
    column_index = None
    use_ai = True
    
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
        elif sys.argv[i] == '--no-ai':
            use_ai = False
    
    analyze_column_context(file_path, column_name, column_index, use_ai)

if __name__ == "__main__":
    main()
