import streamlit as st
import os
import sys
from sqlalchemy import func
import pandas as pd

# Add the src directory to the Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)

# Import our modules
from database import Student, AttendanceRecord, Intervention, get_session, init_db, Base

def main():
    st.set_page_config(
        page_title="Streamlit App Check",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("Streamlit App Database Check")
    st.write("This tool helps diagnose database connectivity issues in the Streamlit Cloud environment.")
    
    # Initialize the database
    try:
        engine = init_db()
        st.success("✅ Database engine initialized successfully!")
    except Exception as e:
        st.error(f"❌ Error initializing database: {str(e)}")
        st.stop()
    
    # Check environment
    st.header("Environment Information")
    env_vars = {
        "STREAMLIT_RUNTIME": os.environ.get("STREAMLIT_RUNTIME", "Not set"),
        "IS_STREAMLIT_CLOUD": os.environ.get("IS_STREAMLIT_CLOUD", "Not set"),
        "PYTHONPATH": os.environ.get("PYTHONPATH", "Not set"),
        "WORKING_DIR": os.getcwd()
    }
    
    st.json(env_vars)
    
    # Database stats
    st.header("Database Statistics")
    
    try:
        with get_session() as session:
            # Count records
            student_count = session.query(func.count(Student.id)).scalar()
            attendance_count = session.query(func.count(AttendanceRecord.id)).scalar()
            intervention_count = session.query(func.count(Intervention.id)).scalar()
            
            # Display counts
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Students", student_count)
            with col2:
                st.metric("Attendance Records", attendance_count)
            with col3:
                st.metric("Interventions", intervention_count)
            
            # List sample students
            if student_count > 0:
                st.subheader("Sample Students")
                sample_students = session.query(Student).limit(5).all()
                
                student_data = []
                for student in sample_students:
                    student_data.append({
                        "ID": student.id,
                        "Name": f"{student.first_name} {student.last_name}",
                        "Grade": student.grade
                    })
                
                st.table(pd.DataFrame(student_data))
            else:
                st.warning("No students found in the database.")
            
            # Show table schema
            st.subheader("Database Tables")
            table_names = Base.metadata.tables.keys()
            st.write(f"Tables: {', '.join(table_names)}")
    except Exception as e:
        st.error(f"❌ Error querying database: {str(e)}")
    
    # File upload for data import
    st.header("Data Import Tool")
    st.write("Use this tool to import attendance data directly.")
    
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    
    if uploaded_file:
        st.subheader("File Preview")
        try:
            # Save the file temporarily
            with open(f"temp_upload.xlsx", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Preview the file
            df = pd.read_excel("temp_upload.xlsx", nrows=5)
            st.dataframe(df)
            
            # Import button
            if st.button("Import Data"):
                try:
                    # Import the data (simulate)
                    from data_import import parse_filename_date
                    filename = uploaded_file.name
                    start_date, end_date = parse_filename_date(filename)
                    
                    if start_date and end_date:
                        st.success(f"File dates parsed successfully: {start_date} to {end_date}")
                    else:
                        st.warning("Could not parse date range from filename. Using default values.")
                    
                    # Attempt to import data
                    from data_import import import_excel_data
                    
                    with st.spinner("Importing data..."):
                        result = import_excel_data("temp_upload.xlsx")
                        
                        if result:
                            students_added, students_updated, records_added = result
                            st.success(f"✅ Data imported successfully! Added {students_added} students, updated {students_updated} students, created {records_added} attendance records.")
                        else:
                            st.error("❌ Error importing data. Check the console for details.")
                    
                except Exception as e:
                    st.error(f"❌ Error during import: {str(e)}")
                    
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

if __name__ == "__main__":
    main()
