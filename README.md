# Student Attendance Tracking System

A comprehensive system for tracking and analyzing student attendance, with special focus on chronic absenteeism.

## Features

- Track attendance for all students
- Analyze attendance patterns and trends
- Identify and monitor chronically absent students (Tier system)
- Track interventions for students with attendance issues
- Generate reports and visualizations
- Analyze demographic patterns in attendance

## Tier System

- Tier 1: Students missing 10% or more of school days
- Tier 2: Students missing 15% or more of school days
- Tier 3: Students missing 20% or more of school days (Chronic Absenteeism)

## Installation

1. Install Python 3.8 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Import your attendance data:
   - Place your Excel/Numbers files in the `data` directory
   - Run the import script:
     ```bash
     python src/data_import.py
     ```

2. Launch the web interface:
   ```bash
   streamlit run src/app.py
   ```

3. Access the system through your web browser at `http://localhost:8501`

## Features by Page

### Dashboard
- Overview of attendance trends
- Quick summary of chronic absenteeism
- Daily, weekly, monthly, and yearly views

### Student Details
- Individual student attendance records
- Attendance rate calculation
- Status indicators for attendance concerns

### Chronic Absenteeism
- List of students with attendance concerns
- Filtered by grade level
- Tier-based classification

### Demographics
- Attendance patterns by:
  - Grade level
  - Gender
  - Race
  - Time periods

### Interventions
- Track intervention history
- Add new interventions
- Monitor intervention outcomes

## Data Structure

The system uses SQLite database with the following main tables:
- Students: Basic student information
- AttendanceRecords: Daily attendance records
- Interventions: Tracking of attendance interventions

## Support

For questions or issues, please contact your system administrator.
