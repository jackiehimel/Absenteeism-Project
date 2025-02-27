from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import pandas as pd
from sqlalchemy import extract

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    grade = Column(Integer)
    gender = Column(String)
    race = Column(String)
    welfare_status = Column(String)
    nyf_status = Column(String)
    osis_id = Column(String)
    # New demographic fields
    honor_roll = Column(Boolean, default=False)
    housing_status = Column(String)
    sports_participation = Column(Boolean, default=False)
    behavioral_concerns = Column(Boolean, default=False)
    myschool_reports_count = Column(Integer, default=0)
    caregiver_involvement = Column(String)  # High, Medium, Low
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    interventions = relationship("Intervention", back_populates="student")

class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    date = Column(Date)
    total_days = Column(Integer)
    present_days = Column(Integer)
    absent_days = Column(Integer)
    present_percentage = Column(Float)
    absent_percentage = Column(Float)
    school_year = Column(Integer)  # Added to track academic year
    student = relationship("Student", back_populates="attendance_records")

class Intervention(Base):
    __tablename__ = 'interventions'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    intervention_type = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    is_ongoing = Column(Boolean, default=True)
    notes = Column(String)
    student = relationship("Student", back_populates="interventions")

def init_db():
    engine = create_engine('sqlite:///attendance.db')
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine('sqlite:///attendance.db')
    Session = sessionmaker(bind=engine)
    return Session()

def get_attendance_trends(grade=None, start_date=None, end_date=None, interval='monthly'):
    """Get attendance trends with support for different time intervals"""
    print(f"Getting attendance trends with interval: {interval}")
    session = get_session()
    
    # Base query
    query = session.query(
        AttendanceRecord.date,
        func.sum(AttendanceRecord.present_days).label('present_days'),
        func.sum(AttendanceRecord.total_days).label('total_days')
    )
    
    # Apply grade filter if specified
    if grade is not None:
        query = query.join(Student).filter(Student.grade == grade)
    
    # Apply date filters
    if start_date:
        query = query.filter(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.date <= end_date)
    
    # Group by date
    query = query.group_by(AttendanceRecord.date)
    
    # Execute query
    results = query.all()
    
    if not results:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame([(r.date, r.present_days, r.total_days) for r in results],
                      columns=['date', 'present_days', 'total_days'])
    
    # Calculate attendance rate
    df['attendance_rate'] = (df['present_days'] / df['total_days'] * 100).round(1)
    
    # Handle all dates having the same month and day, just different years
    # This is our September 1st every year edge case
    if len(df) > 1 and interval.lower() == 'yearly':
        # Extract all years
        years = list(df.index.year)
        print(f"All years in data: {years}")
        
        # Create a clean yearly dataframe
        data = []
        for year in sorted(years):
            year_data = df[df.index.year == year]
            if not year_data.empty:
                # Calculate yearly attendance and count
                yearly_present = year_data['present_days'].sum()
                yearly_total = year_data['total_days'].sum()
                yearly_rate = (yearly_present / yearly_total * 100).round(1) if yearly_total > 0 else 0
                
                data.append({
                    'period': pd.Timestamp(f"{year}-01-01"),
                    'present_days': yearly_present,
                    'total_days': yearly_total,
                    'attendance_rate': yearly_rate,
                    'student_count': len(year_data)
                })
        
        if data:
            print(f"Created yearly data: {data}")
            return pd.DataFrame(data)
    
    # Debug information
    print(f"Input data: {df.to_dict('records')}")
    
    # Resample based on interval
    df.set_index('date', inplace=True)
    
    # Count students per date before resampling (assumes each date has 1 record per student)
    # Since we've grouped by date, we need to estimate the student count
    student_counts = pd.Series(1, index=df.index)
    
    if interval == 'daily':
        # Add student count column - daily data is already as is
        df['student_count'] = student_counts.values
    elif interval == 'weekly':
        df = df.resample('W').agg({
            'present_days': 'sum',
            'total_days': 'sum'
        })
    elif interval == 'monthly':
        # Check if all dates are on the same day of different months/years
        if df.index.is_monotonic and len(df) > 1 and all(d.day == df.index[0].day for d in df.index):
            # Don't resample, just use the original data
            df['month_year'] = df.index.to_series().apply(lambda x: f"{x.month}-{x.year}")
            # Count number of students per date
            student_count_query = session.query(
                AttendanceRecord.date,
                func.count(AttendanceRecord.student_id.distinct()).label('student_count')
            )
            if grade is not None:
                student_count_query = student_count_query.join(Student).filter(Student.grade == grade)
            student_count_query = student_count_query.group_by(AttendanceRecord.date)
            student_counts = {r.date: r.student_count for r in student_count_query.all()}
            # Add student count to dataframe
            df['student_count'] = df.index.map(lambda x: student_counts.get(x, 0))
            df = df.reset_index()
            df = df.rename(columns={'date': 'period'})
            return df
        else:
            # Regular monthly resampling
            df = df.resample('M').agg({
                'present_days': 'sum',
                'total_days': 'sum'
            })
    elif interval == 'yearly':
        # Regular yearly resampling
        df = df.resample('Y').agg({
            'present_days': 'sum',
            'total_days': 'sum'
        })
    
    # Recalculate attendance rate after resampling
    df['attendance_rate'] = (df['present_days'] / df['total_days'] * 100).round(1)
    
    # Add student count column if not already present
    if 'student_count' not in df.columns:
        # Estimate student count as 1 per period after resampling
        df['student_count'] = 1
    
    df = df.reset_index()
    df = df.rename(columns={'date': 'period'})
    
    print(f"Final output data: {df.to_dict('records')}")
    return df

def get_attendance_trend_data(grade=None):
    """Directly query the database to get attendance trends by year
    Returns manually structured data with one point per year"""
    print("Using get_attendance_trend_data function to get yearly data")
    
    session = get_session()
    
    # Find all distinct academic years with attendance records
    years_query = session.query(extract('year', AttendanceRecord.date).distinct()).order_by(extract('year', AttendanceRecord.date))
    years = [int(year[0]) for year in years_query.all()]  # Ensure years are integers
    
    print(f"Years found: {years}")
    
    if not years:
        return pd.DataFrame()
    
    # Initialize data list
    data = []
    
    # For each year, get the aggregate attendance data
    for year in years:
        query = session.query(
            func.sum(AttendanceRecord.present_days).label('present_days'),
            func.sum(AttendanceRecord.total_days).label('total_days'),
            func.count(Student.id.distinct()).label('student_count')
        ).join(Student)
        
        # Filter by year and grade if specified
        query = query.filter(extract('year', AttendanceRecord.date) == year)
        if grade is not None:
            query = query.filter(Student.grade == grade)
        
        result = query.one()
        
        # Calculate attendance rate
        present_days = result.present_days or 0
        total_days = result.total_days or 0
        student_count = result.student_count or 0
        
        if total_days > 0:
            attendance_rate = (present_days / total_days * 100).round(1)
        else:
            attendance_rate = 0
        
        # Add to data list
        data.append({
            'period': pd.Timestamp(year=year, month=1, day=1),  # January 1st of the year
            'present_days': present_days,
            'total_days': total_days,
            'attendance_rate': attendance_rate,
            'student_count': student_count
        })
    
    print(f"Yearly data created: {data}")
    return pd.DataFrame(data)

def get_tiered_attendance(grade=None, school_year=None):
    """Get students grouped by attendance tiers.
    
    Args:
        grade: Optional grade level to filter by
        school_year: Optional school year to filter by
    
    Returns:
        dict: Dictionary with keys 'tier3' (chronic), 'tier2' (at risk), 'tier1' (warning), 'on_track'
              Each containing a list of dicts with student info and attendance data
    """
    session = get_session()
    
    # Base query to get latest attendance record for each student within the school year
    subquery = session.query(
        AttendanceRecord.student_id,
        func.max(AttendanceRecord.date).label('max_date')
    )
    
    # Apply school year filter to subquery if specified
    if school_year is not None:
        subquery = subquery.filter(AttendanceRecord.school_year == school_year)
    
    subquery = subquery.group_by(AttendanceRecord.student_id).subquery()
    
    # Get the full records that match the latest dates
    query = session.query(
        Student,
        AttendanceRecord
    ).join(
        AttendanceRecord
    ).join(
        subquery,
        (AttendanceRecord.student_id == subquery.c.student_id) &
        (AttendanceRecord.date == subquery.c.max_date)
    )
    
    # Apply grade filter if specified
    if grade is not None:
        query = query.filter(Student.grade == grade)
    
    # Apply school year filter to main query if specified
    if school_year is not None:
        query = query.filter(AttendanceRecord.school_year == school_year)
    
    results = query.all()
    
    # Initialize tiers
    tiers = {
        'tier3': [],  # Chronic: < 80%
        'tier2': [],  # At Risk: 80-84.99%
        'tier1': [],  # Warning: 85-89.99%
        'on_track': [] # On Track: >= 90%
    }
    
    # Categorize students into tiers
    for student, record in results:
        attendance_rate = record.present_percentage
        student_info = {
            'student': student,
            'attendance_rate': attendance_rate,
            'last_updated': record.date
        }
        
        if attendance_rate < 80:
            tiers['tier3'].append(student_info)
        elif attendance_rate < 85:
            tiers['tier2'].append(student_info)
        elif attendance_rate < 90:
            tiers['tier1'].append(student_info)
        else:
            tiers['on_track'].append(student_info)
    
    return tiers
