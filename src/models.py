from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    grade = Column(Integer)
    gender = Column(String)
    race = Column(String)
    # New demographic fields
    honor_roll = Column(Boolean, default=False)
    housing_status = Column(String)
    sports_participation = Column(Boolean, default=False)
    behavioral_concerns = Column(Boolean, default=False)
    myschool_reports_count = Column(Integer, default=0)
    caregiver_involvement = Column(String)  # High, Medium, Low
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    interventions = relationship("Intervention", back_populates="student")

class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    date = Column(Date)
    status = Column(String)  # Present, Absent, Tardy
    school_year = Column(Integer)  # Added to track academic year
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")

class Intervention(Base):
    __tablename__ = 'interventions'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    date = Column(Date)
    type = Column(String)
    description = Column(String)
    outcome = Column(String)
    
    # Relationships
    student = relationship("Student", back_populates="interventions")
