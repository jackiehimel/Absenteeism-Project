import pandas as pd
from datetime import datetime, timedelta
from database import Student, AttendanceRecord, get_session
import os
import re

def parse_filename_date(filename):
    """Extract date range from filename format '9:1:2023-6:19:2024' or '9:1:2024 6:19:2025' or '9_1_2024 6_19_2025'."""
    # Try the standard format with colons
    pattern1 = r'(\d+):(\d+):(\d+)-(\d+):(\d+):(\d+)'
    # Try the alternative format with space
    pattern2 = r'(\d+):(\d+):(\d+)\s+(\d+):(\d+):(\d+)'
    # Try the format with underscores
    pattern3 = r'(\d+)_(\d+)_(\d+)\s*[-\s]\s*(\d+)_(\d+)_(\d+)'
    
    for pattern in [pattern1, pattern2, pattern3]:
        match = re.search(pattern, filename)
        if match:
            start_month, start_day, start_year, end_month, end_day, end_year = map(int, match.groups())
            return (
                datetime(start_year, start_month, start_day).date(),
                datetime(end_year, end_month, end_day).date()
            )
    
    # If no match found, try extracting just the year ranges
    year_pattern = r'(\d{4}).*?(\d{4})'
    match = re.search(year_pattern, filename)
    if match:
        start_year, end_year = map(int, match.groups())
        return (
            datetime(start_year, 9, 1).date(),  # Assume Sept 1st start
            datetime(end_year, 6, 19).date()    # Assume June 19th end
        )
    
    print(f"Could not parse date from filename: {filename}")
    return None, None

def get_welfare_code(status):
    """Return the welfare status as is without mapping to hardcoded values."""
    return status if status is not None else None

def import_excel_data(file_path):
    """Import attendance data from Excel/Numbers files
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        tuple: (students_added, students_updated, records_added) or None if error
    """
    filename = os.path.basename(file_path)
    print(f"\nProcessing {filename}...")
    
    # Extract date range from filename
    start_date, end_date = parse_filename_date(filename)
    
    if file_path.endswith('.numbers'):
        print(f"⚠️  Please export {filename} to Excel format first")
        return None
    
    session = get_session()
    students_added = 0
    students_updated = 0
    records_added = 0
    
    try:
        # Read the Excel file with no header
        df = pd.read_excel(file_path, header=None)
        print(f"Found {len(df)} records")
        
        # Find the row with column headers (usually row 1)
        header_row = None
        for idx, row in df.iterrows():
            if isinstance(row[0], str) and 'user_id' in str(row[0]).lower():
                header_row = idx
                break
        
        if header_row is None:
            raise ValueError("Could not find header row with 'user_id' column. Check your Excel file format.")
        
        # Get the column names and data
        column_names = df.iloc[header_row]
        data = df.iloc[header_row + 1:].reset_index(drop=True)
        
        # Set the column names
        data.columns = column_names
        
        # Debug column names
        print(f"Found columns: {list(data.columns)}")
        
        for _, row in data.iterrows():
            try:
                # Skip rows with no student ID
                if pd.isna(row.get('user_id')):
                    continue
                
                # Convert user_id to integer, handling both string and float inputs
                try:
                    student_id = int(float(row['user_id']))
                except ValueError:
                    print(f"⚠️  Invalid user_id: {row.get('user_id')}")
                    continue
                
                # Create or update student record
                student = session.query(Student).filter_by(id=student_id).first()
                
                if not student:
                    # Get grade from class_label
                    grade = None
                    if 'class_label' in row and pd.notna(row.get('class_label')):
                        grade_match = re.search(r'Grade *(\d+)', str(row['class_label']))
                        if grade_match:
                            grade = int(grade_match.group(1))
                    
                    # Create new student
                    student = Student(
                        id=student_id,
                        first_name=f"Student",  # Using generic first name for privacy
                        last_name=str(student_id),  # Using ID as last name for privacy
                        grade=grade,
                        welfare_status=get_welfare_code(row.get('Welfare status')) if pd.notna(row.get('Welfare status')) else None,
                        nyf_status=str(row.get('NYF status')).upper() == 'YC' if pd.notna(row.get('NYF status')) else None,
                        osis_id=str(int(float(row['OSIS ID Number']))) if pd.notna(row.get('OSIS ID Number')) else None
                    )
                    session.add(student)
                    students_added += 1
                else:
                    # Update existing student
                    students_updated += 1
                
                # Create attendance record for this period
                if start_date and end_date:
                    try:
                        # Find attendance columns dynamically
                        attendance_cols = {
                            'total': next((col for col in data.columns if isinstance(col, str) and 'total' in col.lower() and 'day' in col.lower()), None),
                            'present': next((col for col in data.columns if isinstance(col, str) and 'present' in col.lower() and 'day' in col.lower()), None),
                            'absent': next((col for col in data.columns if isinstance(col, str) and 'absent' in col.lower() and 'day' in col.lower()), None),
                            'present_pct': next((col for col in data.columns if isinstance(col, str) and 'present' in col.lower() and '%' in col), None),
                            'absent_pct': next((col for col in data.columns if isinstance(col, str) and 'absent' in col.lower() and '%' in col), None)
                        }
                        
                        # Debug found columns
                        print(f"Found attendance columns: {attendance_cols}")
                        
                        # Ensure we have the necessary columns
                        if not attendance_cols['total'] or not attendance_cols['present']:
                            raise ValueError(f"Could not find required columns: {attendance_cols}")
                        
                        # Convert attendance data
                        total_days = int(float(row[attendance_cols['total']])) if attendance_cols['total'] and pd.notna(row.get(attendance_cols['total'])) else 0
                        present_days = int(float(row[attendance_cols['present']])) if attendance_cols['present'] and pd.notna(row.get(attendance_cols['present'])) else 0
                        absent_days = int(float(row[attendance_cols['absent']])) if attendance_cols['absent'] and pd.notna(row.get(attendance_cols['absent'])) else 0
                        
                        # Calculate percentages if not provided
                        if attendance_cols['present_pct'] and pd.notna(row.get(attendance_cols['present_pct'])):
                            present_pct = float(row[attendance_cols['present_pct']])
                        else:
                            present_pct = (present_days / total_days * 100) if total_days > 0 else 0
                            
                        if attendance_cols['absent_pct'] and pd.notna(row.get(attendance_cols['absent_pct'])):
                            absent_pct = float(row[attendance_cols['absent_pct']])
                        else:
                            absent_pct = (absent_days / total_days * 100) if total_days > 0 else 0
                        
                        # Create a single record for the period
                        attendance = AttendanceRecord(
                            student=student,
                            date=start_date,  # Use period start date
                            total_days=total_days,
                            present_days=present_days,
                            absent_days=absent_days,
                            present_percentage=present_pct,
                            absent_percentage=absent_pct,
                            school_year=start_date.year if start_date.month >= 7 else start_date.year - 1  # School year starts in July/August
                        )
                        session.add(attendance)
                        records_added += 1
                        
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  Error processing attendance data for student {student_id}: {e}")
                        continue
            
            except Exception as e:
                print(f"⚠️  Error processing row: {e}")
                continue
        
        session.commit()
        print(f"✅ Successfully imported {records_added} records from {filename}")
        return (students_added, students_updated, records_added)
        
    except Exception as e:
        error_msg = f"❌ Error reading {filename}: {str(e)}"
        print(error_msg)
        session.rollback()
        return None
        
    finally:
        session.close()

def import_all_data(data_directory):
    """Import all Excel/Numbers files from a directory
    
    Args:
        data_directory: Path to directory containing data files
        
    Returns:
        list: List of results from each import_excel_data call
    """
    print(f"Looking for data files in: {data_directory}")
    
    try:
        files = [f for f in os.listdir(data_directory) 
                if f.endswith(('.xlsx', '.xls'))]
        
        if not files:
            print("No Excel files found!")
            return []
        
        print(f"Found {len(files)} files to process")
        
        # Sort files by date (oldest first)
        files.sort()
        
        results = []
        for filename in files:
            file_path = os.path.join(data_directory, filename)
            result = import_excel_data(file_path)
            results.append(result)
        
        print("\nData import completed!")
        return results
        
    except Exception as e:
        print(f"Error during batch import: {str(e)}")
        return []

if __name__ == "__main__":
    import os
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    print(f"Importing data from: {data_dir}")
    import_all_data(data_dir)