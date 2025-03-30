"""
CSV Verifier
------------
A utility for verifying CSV file structure and encoding.
"""

import csv
import os
import chardet
import argparse
from collections import Counter


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


def verify_csv(file_path, delimiter=','):
    """
    Verify the structure of a CSV file and provide information about it.
    
    Args:
        file_path (str): Path to the CSV file
        delimiter (str): CSV delimiter character
        
    Returns:
        dict: Information about the CSV file
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        print("Please check if:")
        print("1. The file path is correct")
        print("2. The file name includes any extension (like .csv)")
        print("3. You have permission to access this file")
        return None
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Detect encoding
    encoding = detect_encoding(file_path)
    
    # Read the CSV
    with open(file_path, 'r', encoding=encoding) as infile:
        # First try to read the file with the specified delimiter
        sample = infile.read(4096)
        infile.seek(0)
        
        # Check if the delimiter exists in the sample
        if delimiter not in sample:
            print(f"Warning: Delimiter '{delimiter}' not found in file sample. Trying to auto-detect...")
            # Try to detect the delimiter
            potential_delimiters = [',', ';', '\t', '|']
            delimiter_counts = {d: sample.count(d) for d in potential_delimiters}
            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
            if delimiter_counts[best_delimiter] > 0:
                print(f"Auto-detected delimiter: '{best_delimiter}'")
                delimiter = best_delimiter
            else:
                print("Could not auto-detect delimiter. Using specified delimiter.")
        
        # Use csv.reader to properly handle quoted fields and other CSV complexities
        infile.seek(0)
        reader = csv.reader(infile, delimiter=delimiter)
        headers = next(reader)
        
        # Check if headers might be a single column that needs splitting
        if len(headers) == 1 and delimiter in headers[0]:
            print(f"Warning: Headers appear to be a single column. Splitting with delimiter: '{delimiter}'")
            headers = headers[0].split(delimiter)
        
        # Read all rows
        rows = []
        for row in reader:
            # If row has only one element but contains delimiter, split it
            if len(row) == 1 and delimiter in row[0]:
                rows.append(row[0].split(delimiter))
            else:
                rows.append(row)
        
        row_count = len(rows)
        
        # Check column consistency
        column_counts = [len(row) for row in rows]
        
        # Special case for single-column CSVs
        is_single_column_csv = len(headers) == 1 and headers[0] == "Content"
        if is_single_column_csv:
            # For single-column CSVs created by our transform function, 
            # we'll consider it consistent if all rows have at least one column
            consistent_columns = all(len(row) >= 1 for row in rows)
        else:
            consistent_columns = len(set(column_counts)) == 1
        
        # Check for empty cells
        empty_cells = sum(1 for row in rows for cell in row if not cell.strip())
        
        # Check data types in each column
        column_data_types = []
        for i in range(len(headers)):
            column_values = [row[i] for row in rows if i < len(row)]
            
            # Try to determine if column is numeric, date, or string
            numeric_count = sum(1 for val in column_values if val.strip().replace('.', '', 1).isdigit())
            if numeric_count > 0.8 * len(column_values):
                column_data_types.append("numeric")
            else:
                column_data_types.append("string")
    
    # Compile results
    results = {
        "file_path": file_path,
        "file_size_bytes": file_size,
        "encoding": encoding,
        "delimiter": delimiter,
        "header_count": len(headers),
        "headers": headers,
        "row_count": row_count,
        "consistent_columns": consistent_columns,
        "is_single_column_csv": is_single_column_csv,
        "empty_cells": empty_cells,
        "column_data_types": dict(zip(headers, column_data_types))
    }
    
    return results


def print_verification_results(results):
    """Print the verification results in a readable format."""
    print("\n=== CSV File Verification Results ===")
    print(f"File: {results['file_path']}")
    print(f"Size: {results['file_size_bytes']} bytes")
    print(f"Encoding: {results['encoding']}")
    print(f"Delimiter: '{results['delimiter']}'")
    print(f"Headers ({results['header_count']}): {', '.join(results['headers'])}")
    print(f"Rows: {results['row_count']}")
    
    # Special handling for single-column CSVs
    if results.get('is_single_column_csv', False):
        print(f"Format: Single-column CSV (Content)")
        print(f"Column consistency: ✓")
    else:
        print(f"Column consistency: {'✓' if results['consistent_columns'] else '✗'}")
    
    print(f"Empty cells: {results['empty_cells']}")
    
    print("\nColumn Data Types:")
    for header, data_type in results['column_data_types'].items():
        print(f"  - {header}: {data_type}")
    
    print("\nStructure Assessment:")
    if results.get('is_single_column_csv', False):
        print("✓ The single-column CSV structure appears to be correct.")
    elif results['consistent_columns'] and results['empty_cells'] == 0:
        print("✓ The CSV structure appears to be correct.")
    else:
        print("⚠ The CSV structure has some issues:")
        if not results['consistent_columns']:
            print("  - Inconsistent number of columns across rows")
        if results['empty_cells'] > 0:
            print(f"  - Contains {results['empty_cells']} empty cells")
    
    # Add a preview of the file content
    print("\nContent Preview (first 5 rows):")
    try:
        with open(results['file_path'], 'r', encoding=results['encoding']) as f:
            reader = csv.reader(f, delimiter=results['delimiter'])
            headers = next(reader)
            print(f"  Headers: {', '.join(headers)}")
            
            # Print first 5 data rows
            for i, row in enumerate(reader):
                if i < 5:
                    # Format row for display
                    if len(row) > 3:
                        # For many columns, show first 3 and count
                        preview = f"{', '.join(row[:3])}... ({len(row)} columns)"
                    else:
                        preview = ', '.join(row)
                    print(f"  Row {i+1}: {preview}")
                else:
                    break
            
            # Show total row count
            if results['row_count'] > 5:
                print(f"  ... and {results['row_count'] - 5} more rows")
    except Exception as e:
        print(f"  Error previewing content: {str(e)}")


def verify_txt(file_path):
    """
    Verify the structure of a TXT file and provide information about it.
    
    Args:
        file_path (str): Path to the TXT file
        
    Returns:
        dict: Information about the TXT file
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        print("Please check if:")
        print("1. The file path is correct")
        print("2. The file name includes any extension (like .txt)")
        print("3. You have permission to access this file")
        return None
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # For large files, use a sampling approach
    large_file_threshold = 10 * 1024 * 1024  # 10 MB
    is_large_file = file_size > large_file_threshold
    
    # Detect encoding
    encoding = detect_encoding(file_path)
    
    # Read the TXT
    with open(file_path, 'r', encoding=encoding) as infile:
        if is_large_file:
            print(f"Large file detected ({file_size / (1024*1024):.2f} MB). Using sampling approach.")
            # Read first 100 lines and last 100 lines for large files
            first_lines = []
            for i, line in enumerate(infile):
                if i < 100:
                    first_lines.append(line)
                else:
                    break
            
            # Get approximate line count for large files
            infile.seek(0)
            line_count = sum(1 for _ in infile)
            
            # Sample lines from the middle
            middle_lines = []
            if line_count > 200:
                infile.seek(0)
                middle_start = max(100, line_count // 2 - 50)
                for i, line in enumerate(infile):
                    if i >= middle_start and i < middle_start + 100:
                        middle_lines.append(line)
                    elif i >= middle_start + 100:
                        break
            
            # Combine samples
            lines = first_lines + middle_lines
        else:
            lines = infile.readlines()
            line_count = len(lines)
        
        # Check for empty lines
        empty_lines = sum(1 for line in lines if not line.strip())
        
        # Check for potential CSV structure
        potential_delimiters = [',', ';', '\t', '|']
        delimiter_counts = {d: sum(line.count(d) for line in lines) for d in potential_delimiters}
        best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        
        # Enhanced CSV detection
        is_potential_csv = False
        csv_confidence = 0
        
        # Check if first line might be a header
        if lines and any(d in lines[0] for d in potential_delimiters):
            # Count delimiters in first line (potential header)
            header_delimiters = {d: lines[0].count(d) for d in potential_delimiters}
            best_header_delimiter = max(header_delimiters, key=header_delimiters.get)
            
            if header_delimiters[best_header_delimiter] > 0:
                # Check if most lines have similar delimiter counts
                expected_count = lines[0].count(best_header_delimiter)
                matching_lines = sum(1 for line in lines[1:] 
                                    if line.strip() and abs(line.count(best_header_delimiter) - expected_count) <= 2)
                
                if matching_lines >= 0.7 * (len(lines) - 1):
                    is_potential_csv = True
                    best_delimiter = best_header_delimiter
                    csv_confidence = matching_lines / max(1, len(lines) - 1)
        
        # Calculate average line length
        avg_line_length = sum(len(line) for line in lines) / max(1, len(lines))
        
        # Check for consistent line lengths
        line_lengths = [len(line) for line in lines]
        consistent_line_length = max(line_lengths) - min(line_lengths) < 10
    
    # Compile results
    results = {
        "file_path": file_path,
        "file_size_bytes": file_size,
        "encoding": encoding,
        "line_count": line_count,
        "empty_lines": empty_lines,
        "avg_line_length": avg_line_length,
        "consistent_line_length": consistent_line_length,
        "potential_csv": is_potential_csv,
        "potential_delimiter": best_delimiter if is_potential_csv else None,
        "csv_confidence": csv_confidence if is_potential_csv else 0,
        "is_large_file": is_large_file
    }
    
    return results


def print_txt_verification_results(results):
    """Print the TXT verification results in a readable format."""
    print("\n=== TXT File Verification Results ===")
    print(f"File: {results['file_path']}")
    print(f"Size: {results['file_size_bytes']} bytes")
    print(f"Encoding: {results['encoding']}")
    print(f"Lines: {results['line_count']}")
    print(f"Empty lines: {results['empty_lines']}")
    print(f"Average line length: {results['avg_line_length']:.2f} characters")
    print(f"Consistent line length: {'✓' if results['consistent_line_length'] else '✗'}")
    
    if results['potential_csv']:
        confidence_pct = results.get('csv_confidence', 0) * 100
        print(f"\nThis TXT file appears to have a CSV-like structure ({confidence_pct:.1f}% confidence).")
        print(f"Potential delimiter: '{results['potential_delimiter']}'")
        
        # Provide direct command suggestions
        print("\nRecommended actions:")
        
        # 1. Verify as CSV
        print("1. Verify as CSV:")
        print(f"   python csv_verifier.py \"{results['file_path']}\" --delimiter \"{results['potential_delimiter']}\"")
        
        # 2. Transform to proper CSV - save in same directory as original
        original_dir = os.path.dirname(results['file_path'])
        original_name = os.path.splitext(os.path.basename(results['file_path']))[0]
        output_path = os.path.join(original_dir, original_name + ".csv")
        print("2. Transform to proper CSV:")
        print(f"   python csv_verifier.py \"{results['file_path']}\" --transform --output \"{output_path}\" --delimiter \"{results['potential_delimiter']}\" --verify-after")
    
    print("\nStructure Assessment:")
    if results['empty_lines'] == 0 and results['consistent_line_length']:
        print("✓ The TXT structure appears to be consistent.")
    else:
        print("⚠ The TXT structure has some issues:")
        if results['empty_lines'] > 0:
            print(f"  - Contains {results['empty_lines']} empty lines")
        if not results['consistent_line_length']:
            print("  - Line lengths are inconsistent")
            if results['potential_csv']:
                print("    (This is normal for CSV-like files with varying field lengths)")
    
    # Add a preview of the file content
    print("\nContent Preview (first 3 lines):")
    try:
        with open(results['file_path'], 'r', encoding=results['encoding']) as f:
            lines = []
            for i, line in enumerate(f):
                if i < 3:
                    # Truncate long lines for display
                    preview = line.strip()
                    if len(preview) > 80:
                        preview = preview[:77] + "..."
                    lines.append(preview)
                else:
                    break
            
            # Print the preview lines
            for i, line in enumerate(lines):
                print(f"  Line {i+1}: {line}")
            
            # Show total line count
            if results['line_count'] > 3:
                print(f"  ... and {results['line_count'] - 3} more lines")
    except Exception as e:
        print(f"  Error previewing content: {str(e)}")


def transform_file(input_file, output_file, target_encoding='utf-8', delimiter=','):
    """
    Transform a file to the target encoding and format.
    
    Args:
        input_file (str): Path to the input file
        output_file (str): Path to save the transformed file
        target_encoding (str): Target encoding (default: utf-8)
        delimiter (str): CSV delimiter character (for CSV files)
    """
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File not found at '{input_file}'")
        return
    
    # Detect source encoding
    source_encoding = detect_encoding(input_file)
    print(f"Detected encoding: {source_encoding}")
    
    # Determine file type based on extension
    file_ext = os.path.splitext(input_file)[1].lower()
    output_ext = os.path.splitext(output_file)[1].lower()
    
    # Clean output path for display
    clean_output_path = output_file
    
    if file_ext in ['.csv', '.tsv']:
        # Handle CSV/TSV files
        with open(input_file, 'r', encoding=source_encoding) as infile:
            # Auto-detect delimiter if not specified
            if delimiter == 'auto':
                sample = infile.read(4096)
                infile.seek(0)
                potential_delimiters = [',', ';', '\t', '|']
                delimiter_counts = {d: sample.count(d) for d in potential_delimiters}
                delimiter = max(delimiter_counts, key=delimiter_counts.get)
                print(f"Auto-detected delimiter: '{delimiter}'")
            
            reader = csv.reader(infile, delimiter=delimiter)
            headers = next(reader)
            rows = list(reader)
        
        # Write to output file with target encoding
        with open(output_file, 'w', encoding=target_encoding, newline='') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            writer.writerow(headers)
            writer.writerows(rows)
    
    elif file_ext in ['.txt'] or file_ext == '':
        # Handle TXT files
        with open(input_file, 'r', encoding=source_encoding) as infile:
            content = infile.read()
        
        # Check if we're converting TXT to CSV
        if output_ext in ['.csv', '.tsv']:
            print("Converting TXT to CSV format...")
            
            # First verify if the TXT has CSV-like structure
            results = verify_txt(input_file)
            
            if results and results['potential_csv']:
                # Use the detected delimiter
                csv_delimiter = results['potential_delimiter']
                print(f"Using detected delimiter: '{csv_delimiter}'")
                
                # Read the file again and parse as CSV
                with open(input_file, 'r', encoding=source_encoding) as infile:
                    lines = infile.readlines()
                    
                    # Parse each line as CSV
                    csv_rows = []
                    max_columns = 0
                    
                    for line in lines:
                        if csv_delimiter in line:
                            row = line.strip().split(csv_delimiter)
                            csv_rows.append(row)
                            max_columns = max(max_columns, len(row))
                        else:
                            csv_rows.append([line.strip()])
                            max_columns = max(max_columns, 1)
                    
                    # Ensure all rows have the same number of columns
                    for i in range(len(csv_rows)):
                        while len(csv_rows[i]) < max_columns:
                            csv_rows[i].append("")
                
                # Write as CSV
                with open(output_file, 'w', encoding=target_encoding, newline='') as outfile:
                    writer = csv.writer(outfile, delimiter=delimiter)
                    # First row as header
                    if csv_rows:
                        writer.writerow(csv_rows[0])
                        # Rest as data
                        writer.writerows(csv_rows[1:])
                
                print(f"Converted TXT to CSV with {len(csv_rows)-1} data rows and {max_columns} columns")
            else:
                print("Warning: TXT file doesn't appear to have CSV structure. Creating a single-column CSV.")
                with open(input_file, 'r', encoding=source_encoding) as infile:
                    lines = [line.strip() for line in infile.readlines()]
                
                # Create a proper single-column CSV with consistent structure
                with open(output_file, 'w', encoding=target_encoding, newline='') as outfile:
                    writer = csv.writer(outfile, delimiter=delimiter)
                    writer.writerow(["Content"])  # Header
                    
                    # Write each line as a single-column row
                    for line in lines:
                        if line:  # Skip empty lines
                            writer.writerow([line])
                
                print(f"Created single-column CSV with {len(lines)} rows")
        else:
            # Just convert encoding
            with open(output_file, 'w', encoding=target_encoding) as outfile:
                outfile.write(content)
    
    else:
        print(f"Unsupported file type: {file_ext}")
        return
    
    # At the end of the function, use the clean path for display
    print(f"Transformed file saved to {clean_output_path} with {target_encoding} encoding")


def find_file(file_path):
    """
    Try to find a file if the exact path doesn't exist.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Found file path or original path if not found
    """
    if os.path.exists(file_path):
        return file_path
    
    # Try to find the file in the directory
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return file_path
    
    # Look for files with similar names
    similar_files = []
    for file in os.listdir(directory):
        if filename.lower() in file.lower():
            similar_files.append(os.path.join(directory, file))
    
    if similar_files:
        print(f"File not found, but found {len(similar_files)} similar files:")
        for i, file in enumerate(similar_files):
            print(f"  {i+1}. {os.path.basename(file)}")
        
        # If only one similar file, suggest using it
        if len(similar_files) == 1:
            print(f"Using: {similar_files[0]}")
            return similar_files[0]
        else:
            # Allow user to select a file
            try:
                selection = input("Enter the number of the file to use (or press Enter to cancel): ")
                if selection.strip():
                    index = int(selection) - 1
                    if 0 <= index < len(similar_files):
                        selected_file = similar_files[index]
                        print(f"Using: {selected_file}")
                        return selected_file
                    else:
                        print("Invalid selection.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            
            print("No file selected.")
    
    return file_path


def main():
    """Command line interface for the file verifier and transformer."""
    parser = argparse.ArgumentParser(description='Verify and transform file structure')
    parser.add_argument('file', help='File to verify or transform')
    parser.add_argument('--delimiter', default=',', help='CSV delimiter (use "auto" for auto-detection)')
    parser.add_argument('--transform', action='store_true', help='Transform the file to UTF-8')
    parser.add_argument('--output', help='Output file for transformation (if not specified, saves in same directory as input)')
    parser.add_argument('--encoding', default='utf-8', help='Target encoding for transformation')
    parser.add_argument('--find', action='store_true', help='Try to find the file if exact path not found')
    parser.add_argument('--verify-after', action='store_true', help='Verify the file after transformation')
    
    args = parser.parse_args()
    
    file_path = args.file
    
    # Try to find the file if requested
    if args.find or not os.path.exists(file_path):
        file_path = find_file(file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return
    
    # Determine file type based on extension
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # If transform option is selected
    if args.transform:
        output_file = args.output
        
        # If output is not specified, create one in the same directory as the input file
        if not output_file:
            input_dir = os.path.dirname(file_path)
            input_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Determine output extension based on input file type
            if file_ext in ['.txt'] or file_ext == '':
                output_ext = '.csv'  # Default to CSV for TXT files
            else:
                output_ext = file_ext  # Keep same extension for other files
                
            output_file = os.path.join(input_dir, input_name + output_ext)
            print(f"No output file specified. Using: {output_file}")
        
        transform_file(file_path, output_file, args.encoding, args.delimiter)
        
        # Verify the transformed file if requested
        if args.verify_after and os.path.exists(output_file):
            print("\nVerifying transformed file...")
            output_ext = os.path.splitext(output_file)[1].lower()
            if output_ext in ['.csv', '.tsv']:
                results = verify_csv(output_file, args.delimiter)
                if results:
                    print_verification_results(results)
            elif output_ext in ['.txt'] or output_ext == '':
                results = verify_txt(output_file)
                if results:
                    print_txt_verification_results(results)
        
        return
    
    # Otherwise, verify the file
    if file_ext in ['.csv', '.tsv']:
        results = verify_csv(file_path, args.delimiter)
        if results:
            print_verification_results(results)
    elif file_ext in ['.txt'] or file_ext == '':
        results = verify_txt(file_path)
        if results:
            print_txt_verification_results(results)
    else:
        print(f"Unsupported file type: {file_ext}")


if __name__ == "__main__":
    main()