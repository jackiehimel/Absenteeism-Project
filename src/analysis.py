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
    # If no end_date is provided, use today
    if not end_date:
        end_date = datetime.now().date()
    
    # If no start_date is provided, default to 6 months before end_date
    if not start_date:
        start_date = (end_date - timedelta(days=180))
    """Analyze attendance trends with flexible time intervals
    interval: 'daily', 'weekly', 'monthly', or 'yearly'
    """
    session = get_session()
    query = session.query(AttendanceRecord)
    
    try:
        if student_id:
            query = query.filter(AttendanceRecord.student_id == student_id)
        
        if grade is not None:  # Allow grade 0
            # Ensure grade is an integer
            grade = int(grade)
            query = query.join(Student).filter(Student.grade == grade)
        
        if start_date:
            # Ensure start_date is a date object
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            query = query.filter(AttendanceRecord.date >= start_date)
        
        if end_date:
            # Ensure end_date is a date object
            if isinstance(end_date, datetime):
                end_date = end_date.date()
            query = query.filter(AttendanceRecord.date <= end_date)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid parameter values: {str(e)}")
    
    records = query.order_by(AttendanceRecord.date).all()
    
    if not records:
        return pd.DataFrame(columns=['period', 'attendance_rate'])
    
    if not records:
        return pd.DataFrame(columns=['period', 'attendance_rate'])

    # Convert records to DataFrame with proper datetime conversion
    df = pd.DataFrame([
        {
            'date': record.date,
            'present_percentage': record.present_percentage,
            'student_id': record.student_id
        } for record in records
    ])
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by time interval and calculate average attendance rate
    if interval == 'daily':
        df['period'] = df['date']
    elif interval == 'weekly':
        df['period'] = df['date'] - pd.to_timedelta(df['date'].dt.dayofweek, unit='D')
    elif interval == 'monthly':
        df['period'] = df['date'].dt.to_period('M').dt.to_timestamp()
    else:  # yearly
        df['period'] = df.apply(
            lambda x: datetime(x['date'].year if x['date'].month >= 9 else x['date'].year - 1, 9, 1),
            axis=1
        )
    
    # Calculate average attendance rate for each period
    result = df.groupby('period').agg(
        attendance_rate=('present_percentage', 'mean'),
        student_count=('student_id', 'nunique'),
        record_count=('present_percentage', 'count')
    ).reset_index()
    
    # Only include periods that have actual data
    result = result[result['record_count'] > 0]
    
    # Sort by period and select final columns
    result = result[['period', 'attendance_rate']].sort_values('period')
    
    # Sort by period and select final columns
    result = result[['period', 'attendance_rate']].sort_values('period')
    
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
        return None
    
    # Convert records to DataFrame
    df = pd.DataFrame(records, columns=['date', 'absent_percentage'])
    
    # Convert date string to datetime and extract day of week
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()
    
    # Define weekday order and filter out weekends
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    df = df[df['day_of_week'].isin(day_order)]
    
    # Calculate average absence rate for each day
    day_patterns = df.groupby('day_of_week')['absent_percentage'].mean()
    
    # Sort by our custom order
    day_patterns = day_patterns.reindex(day_order)
    
    # For debugging
    print("Records per day:")
    print(df.groupby('day_of_week').size())
    print("\nAbsence rates:")
    print(day_patterns)
    
    patterns = {
        'day_of_week': day_patterns
    }
    
    return patterns



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
            'gender': student.gender,
            'race': student.race,
            'attendance_rate': attendance_rate
        })
    
    if not demographic_data:
        return {
            'by_grade': pd.Series(dtype='float64'),
            'by_gender': pd.Series(dtype='float64'),
            'by_race': pd.Series(dtype='float64')
        }
    
    df = pd.DataFrame(demographic_data)
    
    # Analysis by various demographic factors
    analysis = {}
    
    if not grade:  # Only show grade analysis if not filtered by grade
        analysis['by_grade'] = df.groupby('grade')['attendance_rate'].mean()
    
    analysis['by_gender'] = df.groupby('gender')['attendance_rate'].mean() if 'gender' in df.columns else pd.Series(dtype='float64')
    analysis['by_race'] = df.groupby('race')['attendance_rate'].mean() if 'race' in df.columns else pd.Series(dtype='float64')
    
    return analysis
