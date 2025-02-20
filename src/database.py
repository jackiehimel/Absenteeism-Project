from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, Boolean, func
import pandas as pd
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

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
    
    # Resample based on interval
    df.set_index('date', inplace=True)
    
    if interval == 'daily':
        pass  # Keep daily data as is
    elif interval == 'weekly':
        df = df.resample('W').agg({
            'present_days': 'sum',
            'total_days': 'sum'
        })
    elif interval == 'monthly':
        df = df.resample('M').agg({
            'present_days': 'sum',
            'total_days': 'sum'
        })
    elif interval == 'yearly':
        df = df.resample('Y').agg({
            'present_days': 'sum',
            'total_days': 'sum'
        })
    
    # Recalculate attendance rate after resampling
    df['attendance_rate'] = (df['present_days'] / df['total_days'] * 100).round(1)
    df = df.reset_index()
    df = df.rename(columns={'date': 'period'})
    
    return df
