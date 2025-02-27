from database import Student, AttendanceRecord, get_session
from datetime import datetime, timedelta
import pandas as pd

def calculate_attendance_rate(student_id, start_date=None, end_date=None):
    """Calculate attendance rate for a student within a date range"""
    session = get_session()
    query = session.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
    
    if start_date:
        query = query.filter(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.date <= end_date)
    
    # Get the most recent attendance record in the date range
    record = query.order_by(AttendanceRecord.date.desc()).first()
    
    if not record:
        return 0
    
    return record.present_percentage

def get_tiered_attendance(grade=None, school_year=None):
    """Get students grouped by attendance tiers
    Tier 3: Missing 20% or more (Chronic)
    Tier 2: Missing 15-19.99%
    Tier 1: Missing 10-14.99%
    On Track: Missing less than 10%
    """
    session = get_session()
    
    # Get the most recent attendance record for each student within the school year
    subquery = session.query(
        AttendanceRecord.student_id,
        AttendanceRecord.present_percentage.label('attendance_rate'),
        AttendanceRecord.date.label('record_date')
    )
    
    # Apply school year filter if specified
    if school_year is not None:
        subquery = subquery.filter(AttendanceRecord.school_year == school_year)
    
    subquery = subquery.order_by(
        AttendanceRecord.student_id,
        AttendanceRecord.date.desc()
    ).distinct(AttendanceRecord.student_id).subquery()
    
    # Join with students table
    query = session.query(Student, subquery.c.attendance_rate, subquery.c.record_date)
    if grade:
        query = query.filter(Student.grade == grade)
    
    query = query.join(
        subquery,
        Student.id == subquery.c.student_id
    )
    
    results = query.all()
    
    # Group students by tier
    tiers = {
        'tier3': [], # Chronic: Missing 20% or more (≤ 80% attendance)
        'tier2': [], # At Risk: Missing 15-19.99% (80.01-85% attendance)
        'tier1': [], # Warning: Missing 10-14.99% (85.01-90% attendance)
        'on_track': [] # On Track: Missing <10% (>90% attendance)
    }
    
    for student, attendance_rate, record_date in results:
        student_data = {
            'student': student,
            'attendance_rate': attendance_rate,
            'last_updated': record_date
        }
        
        if attendance_rate <= 80:
            tiers['tier3'].append(student_data)
        elif attendance_rate <= 85:
            tiers['tier2'].append(student_data)
        elif attendance_rate <= 90:
            tiers['tier1'].append(student_data)
        else:
            tiers['on_track'].append(student_data)
    
    return tiers

def get_attendance_trends(student_id=None, grade=None, start_date=None, end_date=None, interval='monthly'):
    """Analyze attendance trends with flexible time intervals
    interval: 'daily', 'weekly', 'monthly', 'quarterly', or 'yearly'
    """
    # If no end_date is provided, use today
    if not end_date:
        end_date = datetime.now().date()
    
    # If no start_date is provided, default to 6 months before end_date
    if not start_date:
        start_date = (end_date - timedelta(days=180))
    
    session = get_session()
    
    # Get all attendance records within date range
    query = session.query(
        AttendanceRecord.date, 
        AttendanceRecord.present_percentage,
        AttendanceRecord.student_id
    )
    
    # Apply filters
    if student_id:
        query = query.filter(AttendanceRecord.student_id == student_id)
    
    if grade is not None:  # Allow grade 0
        query = query.join(Student).filter(Student.grade == grade)
    
    if start_date:
        query = query.filter(AttendanceRecord.date >= start_date)
    
    if end_date:
        query = query.filter(AttendanceRecord.date <= end_date)
    
    # Execute query and get results
    records = query.all()
    
    if not records:
        return pd.DataFrame(columns=['period', 'attendance_rate'])
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([
        {
            'date': record.date,
            'present_percentage': record.present_percentage,
            'student_id': record.student_id
        } for record in records
    ])
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Create period column based on selected interval
    if interval == 'daily':
        df['period'] = df['date']
    elif interval == 'weekly':
        # Start of week (Monday)
        df['period'] = df['date'] - pd.to_timedelta(df['date'].dt.dayofweek, unit='D')
    elif interval == 'monthly':
        # Start of month
        df['period'] = df['date'].dt.strftime('%Y-%m-01')
        df['period'] = pd.to_datetime(df['period'])
    elif interval == 'quarterly':
        # Start of quarter
        df['quarter'] = df['date'].dt.quarter
        df['year'] = df['date'].dt.year
        df['period'] = pd.to_datetime(df.apply(
            lambda x: f"{x['year']}-{(x['quarter']-1)*3+1:02d}-01", 
            axis=1
        ))
    else:  # yearly or default
        # Academic year (starting in September)
        df['period'] = pd.to_datetime(df.apply(
            lambda x: f"{x['date'].year if x['date'].month >= 9 else x['date'].year-1}-09-01",
            axis=1
        ))
    
    # Group by period and calculate average attendance rate
    result = df.groupby('period').agg({
        'present_percentage': 'mean',
        'student_id': 'nunique'
    }).reset_index()
    
    # Rename columns for clarity
    result.columns = ['period', 'attendance_rate', 'student_count']
    
    # Sort by period
    result = result.sort_values('period')
    
    return result

def analyze_absence_patterns(grade=None):
    """Analyze patterns in absences (e.g., specific days of week, months)"""
    session = get_session()
    query = session.query(
        AttendanceRecord.date,
        AttendanceRecord.absent_percentage
    )
    
    if grade:
        query = query.join(Student).filter(Student.grade == grade)
    
    records = query.all()
    
    if not records:
        return pd.DataFrame()  # Return empty DataFrame instead of None
    
    # Convert records to DataFrame
    df = pd.DataFrame(records, columns=['date', 'absent_percentage'])
    
    # Convert date string to datetime and extract day of week and month
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.weekday  # 0=Monday, 6=Sunday
    df['month'] = df['date'].dt.month  # 1=January, 12=December
    
    return df  # Return the dataframe directly

def get_demographic_analysis(grade=None):
    """Analyze attendance patterns by demographics"""
    session = get_session()
    
    students = session.query(Student)
    
    if grade:
        students = students.filter(Student.grade == grade)
    
    demographic_data = []
    for student in students:
        attendance_rate = calculate_attendance_rate(student.id)
        demographic_data.append({
            'grade': student.grade,
            'gender': student.gender or 'Unknown',
            'race': student.race or 'Unknown',
            'welfare_status': student.welfare_status or 'Unknown',
            'nyf_status': student.nyf_status or 'Unknown',
            'behavioral_concerns': 'Yes' if student.behavioral_concerns else 'No',
            'attendance_rate': attendance_rate
        })
    
    if not demographic_data:
        return {
            'gender': pd.DataFrame(),
            'race': pd.DataFrame(),
            'welfare_status': pd.DataFrame(),
            'nyf_status': pd.DataFrame(),
            'behavioral_concerns': pd.DataFrame()
        }
    
    df = pd.DataFrame(demographic_data)
    
    # Analysis by various demographic factors
    result = {}
    
    # Gender analysis
    if 'gender' in df.columns:
        gender_df = df.groupby('gender').agg({
            'attendance_rate': 'mean',
            'gender': 'count'
        }).rename(columns={'gender': 'student_count'}).reset_index()
        result['gender'] = gender_df
    else:
        result['gender'] = pd.DataFrame()
    
    # Race analysis
    if 'race' in df.columns:
        race_df = df.groupby('race').agg({
            'attendance_rate': 'mean',
            'race': 'count'
        }).rename(columns={'race': 'student_count'}).reset_index()
        result['race'] = race_df
    else:
        result['race'] = pd.DataFrame()
    
    # Welfare status analysis
    if 'welfare_status' in df.columns:
        welfare_df = df.groupby('welfare_status').agg({
            'attendance_rate': 'mean',
            'welfare_status': 'count'
        }).rename(columns={'welfare_status': 'student_count'}).reset_index()
        result['welfare_status'] = welfare_df
    else:
        result['welfare_status'] = pd.DataFrame()
    
    # NYF status analysis
    if 'nyf_status' in df.columns:
        nyf_df = df.groupby('nyf_status').agg({
            'attendance_rate': 'mean',
            'nyf_status': 'count'
        }).rename(columns={'nyf_status': 'student_count'}).reset_index()
        result['nyf_status'] = nyf_df
    else:
        result['nyf_status'] = pd.DataFrame()
    
    # Behavioral concerns analysis
    if 'behavioral_concerns' in df.columns:
        behavioral_df = df.groupby('behavioral_concerns').agg({
            'attendance_rate': 'mean',
            'behavioral_concerns': 'count'
        }).rename(columns={'behavioral_concerns': 'student_count'}).reset_index()
        result['behavioral_concerns'] = behavioral_df
    else:
        result['behavioral_concerns'] = pd.DataFrame()
    
    return result
