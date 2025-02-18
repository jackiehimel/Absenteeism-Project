import pandas as pd
from datetime import datetime
from database import Student, AttendanceRecord, get_session
import os
import re

def parse_filename_date(filename):
    """Extract date range from filename format '9:1:2023-6:19:2024' or '9:1:2024 6:19:2025'."""
    # Try the standard format first
    pattern1 = r'(\d+):(\d+):(\d+)-(\d+):(\d+):(\d+)'
    # Try the alternative format with space
    pattern2 = r'(\d+):(\d+):(\d+)\s+(\d+):(\d+):(\d+)'
    
    for pattern in [pattern1, pattern2]:
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
    
    return None, None

def get_welfare_code(status):
    """Convert welfare status codes to full status."""
    codes = {
        'G': 'General',
        'P': 'Poverty',
        'PC': 'Poverty Conditional',
        'FC': 'Foster Care',
        'F': 'Free'
    }
    return codes.get(status, status)

def import_excel_data(file_path):
    """Import attendance data from Excel/Numbers files"""
    filename = os.path.basename(file_path)
    print(f"\nProcessing {filename}...")
    
    # Extract date range from filename
    start_date, end_date = parse_filename_date(filename)
    
    if file_path.endswith('.numbers'):
        print(f"⚠️  Please export {filename} to Excel format first")
        return
    
    try:
        # Read the Excel file with no header
        df = pd.read_excel(file_path, header=None)
        print(f"Found {len(df)} records")
        
        # Find the row with column headers (usually row 1)
        header_row = None
        for idx, row in df.iterrows():
            if isinstance(row[0], str) and 'user_id' in row[0].lower():
                header_row = idx
                break
        
        if header_row is None:
            raise ValueError("Could not find header row with 'user_id' column")
        
        # Get the column names and data
        column_names = df.iloc[header_row]
        data = df.iloc[header_row + 1:].reset_index(drop=True)
        
        # Set the column names
        data.columns = column_names
        
        session = get_session()
        records_added = 0
        
        for _, row in data.iterrows():
            try:
                # Skip rows with no student ID
                if pd.isna(row['user_id']):
                    continue
                
                # Convert user_id to integer, handling both string and float inputs
                try:
                    student_id = int(float(row['user_id']))
                except ValueError:
                    print(f"⚠️  Invalid user_id: {row['user_id']}")
                    continue
                
                # Create or update student record
                student = session.query(Student).filter_by(id=student_id).first()
                
                if not student:
                    # Get grade from class_label
                    grade = None
                    if pd.notna(row.get('class_label')):
                        grade_match = re.search(r'Grade *(\d+)', str(row['class_label']))
                        if grade_match:
                            grade = int(grade_match.group(1))
                    
                    # Create new student
                    student = Student(
                        id=student_id,
                        name=str(student_id),  # Using ID as name for privacy
                        grade=grade,
                        welfare_status=get_welfare_code(row.get('Welfare status')) if pd.notna(row.get('Welfare status')) else None,
                        nyf_status=str(row.get('NYF status')).upper() == 'YC' if pd.notna(row.get('NYF status')) else None,
                        osis_id=str(int(float(row['OSIS ID Number']))) if pd.notna(row.get('OSIS ID Number')) else None
                    )
                    session.add(student)
                
                # Create attendance record for this period
                if start_date and end_date:
                    try:
                        # Find attendance columns dynamically
                        attendance_cols = {
                            'total': next((col for col in data.columns if 'total' in col.lower() and 'day' in col.lower()), None),
                            'present': next((col for col in data.columns if 'present' in col.lower() and 'day' in col.lower()), None),
                            'absent': next((col for col in data.columns if 'absent' in col.lower() and 'day' in col.lower()), None),
                            'present_pct': next((col for col in data.columns if 'present' in col.lower() and '%' in col), None),
                            'absent_pct': next((col for col in data.columns if 'absent' in col.lower() and '%' in col), None)
                        }
                        
                        # Convert attendance data
                        total_days = int(float(row[attendance_cols['total']])) if attendance_cols['total'] and pd.notna(row[attendance_cols['total']]) else 0
                        present_days = int(float(row[attendance_cols['present']])) if attendance_cols['present'] and pd.notna(row[attendance_cols['present']]) else 0
                        absent_days = int(float(row[attendance_cols['absent']])) if attendance_cols['absent'] and pd.notna(row[attendance_cols['absent']]) else 0
                        
                        # Calculate percentages if not provided
                        if attendance_cols['present_pct'] and pd.notna(row[attendance_cols['present_pct']]):
                            present_pct = float(row[attendance_cols['present_pct']])
                        else:
                            present_pct = (present_days / total_days * 100) if total_days > 0 else 0
                            
                        if attendance_cols['absent_pct'] and pd.notna(row[attendance_cols['absent_pct']]):
                            absent_pct = float(row[attendance_cols['absent_pct']])
                        else:
                            absent_pct = (absent_days / total_days * 100) if total_days > 0 else 0
                        
                        attendance = AttendanceRecord(
                            student=student,
                            date=start_date,  # Using period start date
                            total_days=total_days,
                            present_days=present_days,
                            absent_days=absent_days,
                            present_percentage=present_pct,
                            absent_percentage=absent_pct
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
        
    except Exception as e:
        print(f"❌ Error reading {filename}: {str(e)}")
        session.rollback()
        
    finally:
        session.close()

def import_all_data(data_directory):
    """Import all Excel/Numbers files from a directory"""
    print(f"Looking for data files in: {data_directory}")
    
    files = [f for f in os.listdir(data_directory) 
             if f.endswith(('.xlsx', '.numbers'))]
    
    if not files:
        print("No Excel or Numbers files found!")
        return
    
    print(f"Found {len(files)} files to process")
    
    # Sort files by date (oldest first)
    files.sort()
    
    for filename in files:
        file_path = os.path.join(data_directory, filename)
        import_excel_data(file_path)
    
    print("\nData import completed!")

if __name__ == "__main__":
    import os
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    print(f"Importing data from: {data_dir}")
    import_all_data(data_dir)