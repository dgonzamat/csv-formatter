"""
CSV Formatter
------------
A utility for transforming and formatting CSV files with UTF-8 encoding support.
"""

import csv
import os
import chardet
import argparse


def detect_encoding(file_path):
    """
    Detect the encoding of a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Detected encoding
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
    return result['encoding']


def format_csv(input_file, output_file, encoding='utf-8', delimiter=',', 
              transformations=None):
    """
    Format a CSV file with UTF-8 encoding and apply transformations.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to save the formatted CSV file
        encoding (str): Target encoding (default: utf-8)
        delimiter (str): CSV delimiter character
        transformations (callable, optional): Function to transform each row
    """
    # Detect source encoding if not specified
    source_encoding = detect_encoding(input_file)
    print(f"Detected encoding: {source_encoding}")
    
    # Read the CSV with detected encoding
    with open(input_file, 'r', encoding=source_encoding) as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        headers = next(reader)
        rows = list(reader)
    
    # Apply transformations if provided
    if transformations:
        rows = [transformations(row) for row in rows]
    
    # Write to output file with UTF-8 encoding
    with open(output_file, 'w', encoding=encoding, newline='') as outfile:
        writer = csv.writer(outfile, delimiter=delimiter)
        writer.writerow(headers)
        writer.writerows(rows)
    
    print(f"Formatted CSV saved to {output_file} with {encoding} encoding")


def main():
    """Command line interface for the CSV formatter."""
    parser = argparse.ArgumentParser(description='Format CSV files to UTF-8')
    parser.add_argument('input', help='Input CSV file')
    parser.add_argument('output', help='Output CSV file')
    parser.add_argument('--encoding', default='utf-8', help='Target encoding')
    parser.add_argument('--delimiter', default=',', help='CSV delimiter')
    
    args = parser.parse_args()
    
    format_csv(args.input, args.output, args.encoding, args.delimiter)


if __name__ == "__main__":
    main()