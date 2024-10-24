import pandas as pd
import re
from datetime import datetime
import os

class MedicalDataParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.blocks = {}
        
    def read_file(self):
        """Read the entire file content"""
        try:
            with open(self.file_path, 'r') as file:
                return file.readlines()
        except FileNotFoundError:
            print(f"Error: File '{self.file_path}' not found")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

    def is_header_line(self, line):
        """Check if line is a block header (contains asterisks)"""
        return '*' in line
    
    def is_format_line(self, line):
        """Check if line contains format descriptions like (dd/mm/yyyy)"""
        return '(dd/mm/yyyy' in line or '(min)' in line
    
    def extract_block_name(self, line):
        """Extract the block name from header line"""
        return re.sub(r'\*+', '', line).strip()
    
    def parse_columns(self, line):
        """Parse column names from the format line"""
        # Remove parenthetical units and split
        clean_line = re.sub(r'\([^)]*\)', '', line)
        return [col.strip() for col in clean_line.split() if col.strip()]
    
    def parse_data_line(self, line):
        """Parse a data line into values"""
        return [val.strip() for val in line.split('\t') if val.strip()]
    
    def process_blocks(self):
        """Process the file and separate data into blocks"""
        lines = self.read_file()
        if not lines:
            return
        
        current_block = []
        current_block_name = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if self.is_header_line(line):
                # Process previous block if it exists
                if current_block_name and current_block:
                    self.blocks[current_block_name] = self.create_dataframe(current_block)
                
                # Start new block
                current_block_name = self.extract_block_name(line)
                current_block = []
            else:
                current_block.append(line)
        
        # Process the last block
        if current_block_name and current_block:
            self.blocks[current_block_name] = self.create_dataframe(current_block)
    
    def create_dataframe(self, block_lines):
        """Create a pandas DataFrame from block lines"""
        # Initialize variables
        columns = None
        data = []
        
        for line in block_lines:
            if self.is_format_line(line):
                # Skip format description lines
                continue
            elif columns is None:
                # This must be the column names line
                columns = self.parse_columns(line)
            else:
                # This is a data line
                values = self.parse_data_line(line)
                if values and len(values) == len(columns):
                    data.append(values)
        
        if not columns or not data:
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=columns)
        
        # Convert Time column to datetime if it exists
        if 'Time' in df.columns:
            try:
                df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M')
            except ValueError as e:
                print(f"Error converting time values: {e}")
                print("Time column left as string")
        
        # Convert numeric columns
        for col in df.columns:
            if col != 'Time':
                df[col] = pd.to_numeric(df[col].replace('-', pd.NA), errors='ignore')
        
        return df
    
    def get_block_names(self):
        """Return list of all block names"""
        return list(self.blocks.keys())
    
    def get_block(self, block_name):
        """Return specific block as DataFrame"""
        return self.blocks.get(block_name, pd.DataFrame())
    
    def export_to_excel(self):
        """Export all blocks to Excel file with user-specified filename"""
        if not self.blocks:
            print("No data blocks to export!")
            return False
        
        while True:
            # Get filename from user
            filename = input("\nEnter the output Excel filename (without extension): ").strip()
            
            # Add .xlsx extension if not provided
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            # Check if file exists
            if os.path.exists(filename):
                overwrite = input(f"File '{filename}' already exists. Overwrite? (y/n): ").lower()
                if overwrite != 'y':
                    continue
            
            try:
                # Create Excel writer object
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    # Write each block to a separate sheet
                    for block_name, df in self.blocks.items():
                        # Clean sheet name (Excel has restrictions on sheet names)
                        sheet_name = re.sub(r'[\[\]\:\*\?\/\\]', '', block_name)[:31]
                        
                        # Write DataFrame to Excel sheet
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # Auto-adjust columns width
                        worksheet = writer.sheets[sheet_name]
                        for idx, col in enumerate(df.columns):
                            max_length = max(
                                df[col].astype(str).apply(len).max(),
                                len(str(col))
                            ) + 2
                            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
                
                print(f"\nData successfully exported to '{filename}'")
                print(f"Number of sheets created: {len(self.blocks)}")
                print("\nSheets created:")
                for block_name in self.blocks.keys():
                    print(f"- {block_name}")
                return True
                
            except Exception as e:
                print(f"\nError exporting to Excel: {e}")
                retry = input("Would you like to try again with a different filename? (y/n): ").lower()
                if retry != 'y':
                    return False
    
    def print_summary(self):
        """Print summary of all blocks"""
        print("\nData Block Summary:")
        print("=" * 50)
        
        for name, df in self.blocks.items():
            print(f"\nBlock: {name}")
            print("-" * 50)
            print(f"Number of rows: {len(df)}")
            print(f"Number of columns: {len(df.columns)}")
            print("\nColumns:")
            for col in df.columns:
                print(f"- {col}")
            print("\nFirst few rows:")
            print(df.head(3))
            print("\n")

def main(file_path):
    """Main function to process medical data file and export to Excel"""
    # Create parser instance
    parser = MedicalDataParser(file_path)
    
    # Process the file
    print("Processing data file...")
    parser.process_blocks()
    
    # Print summary of data
    parser.print_summary()
    
    # Export to Excel
    parser.export_to_excel()
    
    return parser

if __name__ == "__main__":
    # Example usage
    file_path = "camaps_data.txt"  # Replace with your file path
    parser = main(file_path)
