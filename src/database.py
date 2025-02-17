from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    grade = Column(Integer)
    gender = Column(String)
    race = Column(String)
    welfare_status = Column(String)
    nyf_status = Column(String)
    osis_id = Column(String)
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
    student = relationship("Student", back_populates="attendance_records")

class Intervention(Base):
    __tablename__ = 'interventions'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    date = Column(Date)
    type = Column(String)
    description = Column(String)
    outcome = Column(String)
    student = relationship("Student", back_populates="interventions")

def init_db():
    engine = create_engine('sqlite:///attendance.db')
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine('sqlite:///attendance.db')
    Session = sessionmaker(bind=engine)
    return Session()
