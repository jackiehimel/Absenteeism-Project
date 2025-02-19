import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os
from data_import import import_excel_data
from database import Student, AttendanceRecord, Intervention, get_session
from analysis import get_attendance_trends, get_tiered_attendance, calculate_attendance_rate, analyze_absence_patterns

def main():
    import os  # Add this at the top
    
    # Initialize database and create tables
    from database import Base, init_db
    engine = init_db()
    Base.metadata.create_all(engine)
    
    # Configure the page
    st.set_page_config(
        page_title="Student Attendance Tracking System",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Check if we have any data
    session = get_session()
    student_count = session.query(Student).count()
    
    # Get the data directory path relative to the src directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    # # Debug information
    # st.write("Current directory:", os.getcwd())
    # st.write("Data directory:", data_dir)
    # st.write("Directory exists:", os.path.exists(data_dir))
    # if os.path.exists(data_dir):
    #     st.write("Files in data directory:", os.listdir(data_dir))
    
    if student_count == 0:
        try:
            from data_import import import_all_data
            with st.spinner("Initializing database and importing data..."):
                if not os.path.exists(data_dir):
                    raise Exception(f"Data directory not found: {data_dir}")
                files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.numbers'))]
                if not files:
                    raise Exception(f"No Excel or Numbers files found in {data_dir}")
                st.write("Found files:", files)
                import_all_data(data_dir)
                st.success("Data imported successfully!")
                st.rerun()  # Changed from experimental_rerun() to rerun()
        except Exception as e:
            st.error(f"Error importing data: {str(e)}")
            st.write("Current working directory:", os.getcwd())
            st.write("Directory contents:", os.listdir())
            return

    # Custom CSS to improve layout
    st.markdown("""
        <style>
        /* Global Styles */
        .block-container {
            padding: 1rem;
        }
        
        /* Typography */
        h1 {
            font-size: 2rem;
            margin-bottom: 2rem;
            color: #111827;
            text-align: center;
            font-weight: 600;
        }
        h2 {
            font-size: 1.5rem;
            margin: 1.5rem 0;
            color: #1f2937;
            font-weight: 600;
        }
        h3 {
            font-size: 1.25rem;
            margin: 1rem 0;
            color: #374151;
            font-weight: 500;
        }
        
        /* Main navigation tabs */
        div[data-testid="stHorizontalBlock"]:has(div[data-baseweb="tab-list"]) {
            margin-bottom: 2rem;
        }
        div[data-baseweb="tab-list"]:first-of-type {
            gap: 1.5rem;
            border-bottom: 3px solid #e5e7eb;
            padding-bottom: 0;
        }
        div[data-baseweb="tab-list"]:first-of-type [data-baseweb="tab"] {
            height: 4rem;
            background-color: transparent;
            border-radius: 8px 8px 0 0;
            color: #4b5563;
            font-size: 1.4rem !important;
            font-weight: 600;
            padding: 1rem 2.5rem;
            border: none;
            margin-bottom: -3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        div[data-baseweb="tab-list"]:first-of-type [aria-selected="true"] {
            background-color: white;
            color: #2563eb;
            border: 3px solid #e5e7eb;
            border-bottom: 3px solid white;
        }
        
        /* Secondary tabs */
        div[data-baseweb="tab-list"]:not(:first-of-type) {
            gap: 0.75rem;
            margin: 0.5rem 0 2rem 0;
            background-color: #f8fafc;
            padding: 0.75rem;
            border-radius: 8px;
        }
        div[data-baseweb="tab-list"]:not(:first-of-type) [data-baseweb="tab"] {
            background-color: transparent;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            color: #64748b;
            font-size: 1rem;
            font-weight: 500;
            padding: 0.5rem 1.5rem;
        }
        div[data-baseweb="tab-list"]:not(:first-of-type) [aria-selected="true"] {
            background-color: #2563eb;
            color: white;
            border-color: #2563eb;
        }
        
        /* Form Elements */
        [data-testid="stDateInput"], .stSelectbox > div > div {
            width: 100%;
        }
        [data-testid="stDateInput"] input, .stSelectbox > div > div {
            padding: 0.5rem;
            font-size: 1rem;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
        }
        
        /* Cards and Containers */
        .info-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            margin-bottom: 1rem;
        }
        .status-card {
            font-size: 1.1rem;
            font-weight: 600;
            padding: 0.75rem 1rem;
            border-radius: 6px;
            margin: 0.5rem 0;
        }
        .status-good {
            background-color: #ecfdf5;
            color: #059669;
        }
        .status-warning {
            background-color: #fef3c7;
            color: #b45309;
        }
        .status-danger {
            background-color: #fee2e2;
            color: #b91c1c;
        }
        
        /* Data Display */
        .stPlotlyChart {
            width: 100%;
        }
        div[data-testid="stMetricValue"] > div {
            font-size: 1.5rem;
            font-weight: 500;
        }
        .dataframe {
            font-size: 0.9rem;
        }
        .dataframe th {
            background-color: #f8fafc;
            font-weight: 600;
            padding: 0.75rem;
        }
        .dataframe td {
            padding: 0.75rem;
        }
        
        /* Student Info */
        .student-info {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            color: #374151;
        }
        .student-info strong {
            font-weight: 600;
            display: inline-block;
            width: 140px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Student Attendance Tracking System")
    
    # Create tabs for navigation
    tabs = st.tabs([
        "Dashboard",
        "Student Details",
        "Chronic Absenteeism",
        "Demographics",
        "Interventions",
        "Data Upload"
    ])
    
    # Show content based on selected tab
    with tabs[0]:
        show_dashboard()
    with tabs[1]:
        show_student_details()
    with tabs[2]:
        show_chronic_absenteeism()
    with tabs[3]:
        show_demographics()
    with tabs[4]:
        show_interventions()
    with tabs[5]:
        show_data_upload()

def show_data_upload():
    st.header("Data Upload")
    
    uploaded_file = st.file_uploader("Upload Attendance Data", type=['xlsx'])
    
    if uploaded_file:
        try:
            # Save the uploaded file
            with st.spinner("Processing uploaded file..."):
                # Get the data directory path
                data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
                os.makedirs(data_dir, exist_ok=True)
                
                # Save file
                file_path = os.path.join(data_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Import the data
                from data_import import import_excel_data
                import_excel_data(file_path)
                
                st.success(f"Successfully imported data from {uploaded_file.name}")
                st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        except Exception as e:
            st.error(f"Error importing data: {str(e)}")
            st.error("Please make sure your file follows the required format and column names.")
    
    # Show upload instructions with more detail
    st.markdown("""
        ### Upload Instructions
        Please ensure your Excel file follows these requirements:
        
        - File name format: '9:1:2023-6:19:2024.xlsx' (start_date-end_date)
        - Required columns (case-sensitive):
            - user_id
            - class_label
            - total_days
            - present_days
            - absent_days
        - Optional columns:
            - Welfare status
            - NYF status
            - OSIS ID Number
    """, unsafe_allow_html=True)

def show_dashboard():
    # Get earliest and latest dates from the database
    session = get_session()
    earliest_record = session.query(AttendanceRecord.date).order_by(AttendanceRecord.date.asc()).first()
    latest_record = session.query(AttendanceRecord.date).order_by(AttendanceRecord.date.desc()).first()
    
    if earliest_record and latest_record:
        earliest_date = earliest_record[0]
        latest_date = latest_record[0]
        
        # Adjust the date range to show the full academic year
        if earliest_date.month >= 9:  # If we start in or after September
            start_year = earliest_date.year
        else:
            start_year = earliest_date.year - 1
        earliest_date = earliest_date.replace(year=start_year, month=9, day=1)
        
        if latest_date.month >= 9:  # If we end in or after September
            end_year = latest_date.year + 1
        else:
            end_year = latest_date.year
        latest_date = latest_date.replace(year=end_year, month=6, day=19)
    else:
        # Fallback dates only if database is completely empty
        earliest_date = datetime.now().date().replace(month=9, day=1)  # Default to Sept 1st of current year
        latest_date = earliest_date.replace(year=earliest_date.year + 1, month=6, day=19)  # Default to June 19th next year
    
    # Time period selector
    st.markdown("""
        <h3 style='margin: 1rem 0; color: #374151; font-size: 1.2rem; font-weight: 600;'>Time Period</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input(
            "Start Date",
            min(datetime.now().date(), earliest_date),  # Default to earlier of current date or earliest record
            min_value=earliest_date,
            max_value=latest_date,
            key="start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            latest_date,
            min_value=earliest_date,
            max_value=latest_date,
            key="end_date"
        )
    with col3:
        interval = st.selectbox(
            "Time Interval",
            ["Daily", "Weekly", "Monthly", "Yearly"],
            key="interval"
        )
    
    # Get available grades
    available_grades = [grade[0] for grade in session.query(Student.grade).distinct().order_by(Student.grade)]
    
    # Create tabs for All Grades and individual grades
    tabs = ["All Grades"] + [f"Grade {g}" for g in available_grades]
    active_tab = st.tabs(tabs)
    
    for i, tab in enumerate(active_tab):
        with tab:
            # Convert grade to int for database query
            grade = None if i == 0 else int(available_grades[i-1])
            
            try:
                # Get attendance trends
                trends = get_attendance_trends(
                    grade=grade,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval.lower()
                )
                
                if not trends.empty:
                    # Create attendance trend line plot
                    fig = go.Figure()
                    
                    # Add the main line
                    fig.add_trace(go.Scatter(
                        x=trends['period'],
                        y=trends['attendance_rate'],
                        mode='lines+markers',
                        name='Attendance Rate',
                        line=dict(color='#2563eb', width=3),
                        marker=dict(size=8)
                    ))
                    
                    # Add reference lines
                    fig.add_hline(y=90, line_dash="dash", line_color="#22c55e", 
                                annotation_text="On Track (90%)", annotation_position="top right")
                    fig.add_hline(y=85, line_dash="dash", line_color="#eab308", 
                                annotation_text="Warning (85%)", annotation_position="top right")
                    fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", 
                                annotation_text="At Risk (80%)", annotation_position="top right")
                    
                    # Update layout
                    fig.update_layout(
                        title={
                            'text': f'Attendance Trends {"(All Grades)" if grade is None else f"(Grade {grade})"}',
                            'y': 0.95,
                            'x': 0.5,
                            'xanchor': 'center',
                            'yanchor': 'top'
                        },
                        margin=dict(l=20, r=20, t=40, b=20),
                        yaxis_title='Attendance Rate (%)',
                        xaxis_title='Date',
                        showlegend=False,
                        yaxis=dict(range=[75, 100]),
                        plot_bgcolor='white',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show attendance tiers
                    tiers = get_tiered_attendance(grade=grade)
                    if tiers:
                        total_students = sum(len(tier) for tier in tiers.values())
                        
                        # Tier metrics header
                        st.subheader("Attendance Tiers")
                        
                        # Create tier boxes with better styling
                        tier_cols = st.columns(4)
                        
                        with tier_cols[0]:
                            chronic_count = len(tiers['tier3'])
                            st.markdown(f"""
                                <div style='background-color: #fee2e2; border: 1px solid #fecaca; padding: 1rem; border-radius: 0.5rem;'>
                                    <h4 style='color: #991b1b; margin: 0; font-size: 1rem;'>Tier 3 (Chronic)</h4>
                                    <p style='color: #dc2626; margin: 0.5rem 0; font-size: 1.25rem; font-weight: 600;'>{chronic_count} students</p>
                                    <p style='margin: 0; color: #991b1b;'>{chronic_count/total_students*100:.1f}%</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with tier_cols[1]:
                            at_risk_count = len(tiers['tier2'])
                            st.markdown(f"""
                                <div style='background-color: #fef3c7; border: 1px solid #fde68a; padding: 1rem; border-radius: 0.5rem;'>
                                    <h4 style='color: #92400e; margin: 0; font-size: 1rem;'>Tier 2 (At Risk)</h4>
                                    <p style='color: #d97706; margin: 0.5rem 0; font-size: 1.25rem; font-weight: 600;'>{at_risk_count} students</p>
                                    <p style='margin: 0; color: #92400e;'>{at_risk_count/total_students*100:.1f}%</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with tier_cols[2]:
                            warning_count = len(tiers['tier1'])
                            st.markdown(f"""
                                <div style='background-color: #dbeafe; border: 1px solid #bfdbfe; padding: 1rem; border-radius: 0.5rem;'>
                                    <h4 style='color: #1e40af; margin: 0; font-size: 1rem;'>Tier 1 (Warning)</h4>
                                    <p style='color: #2563eb; margin: 0.5rem 0; font-size: 1.25rem; font-weight: 600;'>{warning_count} students</p>
                                    <p style='margin: 0; color: #1e40af;'>{warning_count/total_students*100:.1f}%</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with tier_cols[3]:
                            on_track_count = len(tiers['on_track'])
                            st.markdown(f"""
                                <div style='background-color: #dcfce7; border: 1px solid #bbf7d0; padding: 1rem; border-radius: 0.5rem;'>
                                    <h4 style='color: #166534; margin: 0; font-size: 1rem;'>On Track</h4>
                                    <p style='color: #16a34a; margin: 0.5rem 0; font-size: 1.25rem; font-weight: 600;'>{on_track_count} students</p>
                                    <p style='margin: 0; color: #166534;'>{on_track_count/total_students*100:.1f}%</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Show absence patterns
                        patterns = analyze_absence_patterns(grade=grade)
                        if patterns:
                            st.subheader("Absence Patterns")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Day of week pattern
                                fig = go.Figure(data=[
                                    go.Bar(
                                        x=patterns['day_of_week'].index,
                                        y=patterns['day_of_week'].values,
                                        marker_color='#2563eb'
                                    )
                                ])
                                
                                fig.update_layout(
                                    title="Absences by Day of Week",
                                    xaxis_title="Day of Week",
                                    yaxis_title="Absence Rate (%)",
                                    showlegend=False,
                                    margin=dict(l=0, r=0, t=40, b=0),
                                    height=300,
                                    plot_bgcolor='white',
                                    yaxis=dict(gridcolor='#e5e7eb')
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            
                            with col2:
                                # Monthly pattern
                                fig = go.Figure(data=[
                                    go.Bar(
                                        x=patterns['month'].index,
                                        y=patterns['month'].values,
                                        marker_color='#2563eb'
                                    )
                                ])
                                
                                fig.update_layout(
                                    title="Absences by Month",
                                    xaxis_title="Month",
                                    yaxis_title="Absence Rate (%)",
                                    showlegend=False,
                                    margin=dict(l=0, r=0, t=40, b=0),
                                    height=300,
                                    plot_bgcolor='white',
                                    yaxis=dict(gridcolor='#e5e7eb')
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No attendance data available for the selected time period.")
            except Exception as e:
                st.error(f"Error loading attendance data: {str(e)}")

def show_student_details():
    st.header("Student Details")
    
    # Get all students
    session = get_session()
    students = session.query(Student).order_by(Student.id).all()
    
    if not students:
        st.info("No students found in the database")
        return
    
    # Student selector
    student_ids = [s.id for s in students]
    student_id = st.selectbox("Select Student", student_ids, key="student_details_select")
    
    if student_id:
        student = session.query(Student).get(student_id)
        
        # Student information section
        st.subheader("Student Information")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display student information
            st.markdown(f"""
                <div class='student-info'><strong>Name:</strong> {student.first_name} {student.last_name}</div>
                <div class='student-info'><strong>Grade:</strong> {student.grade}</div>
                <div class='student-info'><strong>Gender:</strong> {student.gender or 'None'}</div>
                <div class='student-info'><strong>Race:</strong> {student.race or 'None'}</div>
            """, unsafe_allow_html=True)
        
        # Get the most recent attendance record
        latest_record = session.query(AttendanceRecord)\
            .filter(AttendanceRecord.student_id == student.id)\
            .order_by(AttendanceRecord.date.desc())\
            .first()
        
        with col2:
            if latest_record:
                attendance_rate = latest_record.present_percentage
                st.markdown(f"""
                    <div class='student-info'>
                        <strong>Attendance:</strong> {attendance_rate:.1f}%
                    </div>
                """, unsafe_allow_html=True)
                
                # Show attendance status using new status card classes
                if attendance_rate >= 90:
                    st.markdown("<div class='status-card status-good'>Good Attendance</div>", unsafe_allow_html=True)
                elif attendance_rate >= 80:
                    st.markdown("<div class='status-card status-warning'>At Risk</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='status-card status-danger'>Chronic Absence</div>", unsafe_allow_html=True)
            else:
                st.info("No attendance data available")

        # Attendance History section
        st.subheader("Attendance History")
        attendance_records = session.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id
        ).order_by(AttendanceRecord.date.desc()).all()
        
        if attendance_records:
            data = [{
                'Date': record.date,
                'Total Days': record.total_days,
                'Present Days': record.present_days,
                'Absent Days': record.absent_days,
                'Attendance Rate': f"{record.present_percentage:.1f}%"
            } for record in attendance_records]
            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True)
            
            # Attendance trend visualization
            if len(data) > 1:
                st.markdown("<h3>Attendance Trend</h3>", unsafe_allow_html=True)
                trend_data = pd.DataFrame([
                    {
                        'Date': record.date,
                        'Attendance Rate': record.present_percentage
                    } for record in attendance_records
                ])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=trend_data['Date'],
                    y=trend_data['Attendance Rate'],
                    mode='lines+markers',
                    name='Attendance Rate',
                    line=dict(color='#2563eb', width=2),
                    marker=dict(size=6)
                ))
                
                fig.update_layout(
                    margin=dict(l=0, r=0, t=30, b=0),
                    yaxis_title='Attendance Rate (%)',
                    xaxis_title='Date',
                    showlegend=False,
                    yaxis=dict(range=[70, 100]),
                    plot_bgcolor='white',
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No attendance history available")
        
        # Show attendance history
        st.subheader("Attendance History")
        attendance_records = session.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id
        ).order_by(AttendanceRecord.date.desc()).all()
        
        if attendance_records:
            data = [{
                'Date': record.date,
                'Total Days': record.total_days,
                'Present Days': record.present_days,
                'Absent Days': record.absent_days,
                'Attendance Rate': f"{record.present_percentage:.1f}%"
            } for record in attendance_records]
            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True)
            
            # Only show trend if we have data
            if len(data) > 1:
                trend_data = pd.DataFrame([
                    {
                        'Date': record.date,
                        'Attendance Rate': record.present_percentage
                    } for record in attendance_records
                ])
                fig = px.line(trend_data, x='Date', y='Attendance Rate',
                             title='Attendance Rate Over Time')
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No attendance records found")

def show_chronic_absenteeism():
    st.header("Chronic Absenteeism")
    
    # Get available grades from the database
    session = get_session()
    available_grades = [grade[0] for grade in session.query(Student.grade).distinct().order_by(Student.grade)]
    
    if not available_grades:
        st.warning("No student data available in the database")
        return
    
    # Grade selector with only available grades
    grade = st.selectbox(
        "Select Grade", 
        [None] + available_grades, 
        format_func=lambda x: 'All Grades' if x is None else f'Grade {x}'
    )
    
    # Get tiered attendance data
    tiers = get_tiered_attendance(grade=grade)
    
    # Calculate total students and check if we have data
    total_students = sum(len(tier) for tier in tiers.values())
    if total_students == 0:
        st.warning("No attendance data available for the selected criteria")
        return
        
    # Show tier summary at the top
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        chronic_count = len(tiers['tier3'])
        st.metric(
            "Tier 3 (Chronic)",
            f"{chronic_count} students",
            f"{chronic_count/total_students*100:.1f}% of total",
            delta_color="inverse"
        )
    with col2:
        at_risk_count = len(tiers['tier2'])
        st.metric(
            "Tier 2 (At Risk)",
            f"{at_risk_count} students",
            f"{at_risk_count/total_students*100:.1f}% of total",
            delta_color="inverse"
        )
    with col3:
        warning_count = len(tiers['tier1'])
        st.metric(
            "Tier 1 (Warning)",
            f"{warning_count} students",
            f"{warning_count/total_students*100:.1f}% of total",
            delta_color="inverse"
        )
    with col4:
        on_track_count = len(tiers['on_track'])
        st.metric(
            "On Track",
            f"{on_track_count} students",
            f"{on_track_count/total_students*100:.1f}% of total"
        )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Show student lists for at-risk students
    if tiers['tier3'] or tiers['tier2']:
        at_risk_students = tiers['tier3'] + tiers['tier2']
        df = pd.DataFrame([
            {
                'Student ID': t['student'].id,
                'Grade': t['student'].grade,
                'Attendance Rate': t['attendance_rate'],
                'Last Updated': t['last_updated'],
                'Tier': '3 (Chronic)' if t in tiers['tier3'] else '2 (At Risk)',
                'Gender': t['student'].gender,
                'Race': t['student'].race
            } for t in at_risk_students
        ])
        
        # Show Tier 3 students
        if tiers['tier3']:
            st.markdown("<div class='status-card status-danger'>Tier 3 - Chronic Absenteeism (Below 80% Attendance)</div>", unsafe_allow_html=True)
            chronic_df = df[df['Tier'] == '3 (Chronic)'].copy()
            chronic_df['Attendance Rate'] = chronic_df['Attendance Rate'].apply(lambda x: f"{x:.1f}%")
            chronic_df['Last Updated'] = pd.to_datetime(chronic_df['Last Updated']).dt.strftime('%Y-%m-%d')
            st.dataframe(chronic_df.drop('Tier', axis=1), hide_index=True)
        
        # Show Tier 2 students
        if tiers['tier2']:
            st.markdown("<div class='status-card status-warning'>Tier 2 - At Risk (80-84.99% Attendance)</div>", unsafe_allow_html=True)
            at_risk_df = df[df['Tier'] == '2 (At Risk)'].copy()
            at_risk_df['Attendance Rate'] = at_risk_df['Attendance Rate'].apply(lambda x: f"{x:.1f}%")
            at_risk_df['Last Updated'] = pd.to_datetime(at_risk_df['Last Updated']).dt.strftime('%Y-%m-%d')
            st.dataframe(at_risk_df.drop('Tier', axis=1), hide_index=True)
        
        # Show summary statistics
        st.subheader("Demographics of At-Risk Students")
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            # Gender distribution
            if not df['Gender'].isna().all():
                gender_dist = df['Gender'].value_counts()
                fig = px.pie(
                    values=gender_dist.values,
                    names=gender_dist.index,
                    title="Distribution by Gender",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(
                    title={
                        'y': 0.95,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Race distribution
            if not df['Race'].isna().all():
                race_dist = df['Race'].value_counts()
                fig = px.pie(
                    values=race_dist.values,
                    names=race_dist.index,
                    title="Distribution by Race/Ethnicity",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(
                    title={
                        'y': 0.95,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Grade distribution
        if not df['Grade'].isna().all():
            grade_dist = df['Grade'].value_counts().reset_index()
            grade_dist.columns = ['Grade', 'Count']
            fig = px.bar(
                grade_dist,
                x='Grade',
                y='Count',
                title="At-Risk Students by Grade",
                color_discrete_sequence=['#2563eb']
            )
            fig.update_layout(
                title={
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor='white',
                yaxis=dict(gridcolor='#e5e7eb')
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        

        

    else:
        st.success("No students currently requiring immediate intervention.")

def show_demographics():
    st.header("Demographics Analysis")
    
    # Show tiers at the top
    st.subheader("Attendance Tiers")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """<div class='info-card' style='background-color: #fef2f2; padding: 1rem;'>
            <h3 style='color: #dc2626;'>Tier 3 - Chronic</h3>
            <p>Below 80% Attendance</p>
            </div>""", 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """<div class='info-card' style='background-color: #fef3c7; padding: 1rem;'>
            <h3 style='color: #d97706;'>Tier 2 - At Risk</h3>
            <p>80-84.99% Attendance</p>
            </div>""",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """<div class='info-card' style='background-color: #ecfdf5; padding: 1rem;'>
            <h3 style='color: #059669;'>Tier 1 - On Track</h3>
            <p>85%+ Attendance</p>
            </div>""",
            unsafe_allow_html=True
        )
    
    # Get available grades from the database with actual student data
    session = get_session()
    available_grades = [
        grade[0] for grade in session.query(Student.grade)
        .join(AttendanceRecord)
        .distinct()
        .order_by(Student.grade)
        .all()
    ]
    
    if not available_grades:
        st.warning("No grades found with attendance data.")
        return
    
    # Grade selector with only available grades
    grade = st.selectbox(
        "Select Grade", 
        [None] + available_grades, 
        format_func=lambda x: 'All Grades' if x is None else f'Grade {x}',
        key="demographics_grade_select"
    )
    
    # Get demographic analysis
    students = session.query(Student)
    if grade:
        students = students.filter(Student.grade == grade)
    
    # Join with attendance records to only get students with attendance data
    students = students.join(AttendanceRecord).distinct().all()
    
    if not students:
        st.warning("No student data available for the selected criteria")
        return
    
    # Prepare data
    data = []
    for student in students:
        # Get the most recent attendance record
        latest_record = session.query(AttendanceRecord)\
            .filter(AttendanceRecord.student_id == student.id)\
            .order_by(AttendanceRecord.date.desc())\
            .first()
        
        if latest_record:
            data.append({
                'id': student.id,
                'grade': student.grade,
                'gender': student.gender or 'Not Specified',
                'race': student.race or 'Not Specified',
                'attendance_rate': latest_record.present_percentage
            })
    
    if not data:
        st.warning("No attendance data available")
        return
        
    df = pd.DataFrame(data)
    
    # Show overall metrics
    st.subheader("Overall Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Students", 
            len(df),
            help="Total number of students with attendance records"
        )
    with col2:
        avg_rate = df['attendance_rate'].mean()
        st.metric(
            "Average Attendance Rate", 
            f"{avg_rate:.1f}%",
            help="Mean attendance rate across all students"
        )
    with col3:
        below_90 = (df['attendance_rate'] < 90).sum()
        st.metric(
            "Students Below 90%", 
            below_90,
            f"{(below_90/len(df)*100):.1f}% of total",
            delta_color="inverse",
            help="Number of students with attendance below 90%"
        )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Show distributions
    st.subheader("Attendance Distribution")
    
    # By grade
    grade_data = df[df['grade'].notna()]
    if not grade_data.empty and len(grade_data['grade'].unique()) > 1:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        
        # Count students below 85% attendance by grade
        at_risk_by_grade = grade_data[grade_data['attendance_rate'] < 85.0]
        grade_stats = at_risk_by_grade.groupby('grade').size().reset_index()
        grade_stats.columns = ['Grade', 'Count']
        
        # Add percentage
        total_by_grade = grade_data.groupby('grade').size().reset_index()
        total_by_grade.columns = ['Grade', 'Total']
        grade_stats = grade_stats.merge(total_by_grade, on='Grade')
        grade_stats['Percentage'] = (grade_stats['Count'] / grade_stats['Total'] * 100).round(1)
        
        # Create text labels
        text_labels = [f"{count} ({pct}%)" for count, pct in zip(grade_stats["Count"], grade_stats["Percentage"])]
        
        fig = px.bar(
            grade_stats,
            x='Grade',
            y='Count',
            text=text_labels,
            title='At-Risk Students by Grade (Attendance Below 85%)',
            labels={'Count': 'Number of Students'},
            color_discrete_sequence=['#f87171']
        )
        
        fig.update_layout(
            title={
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white',
            yaxis=dict(
                gridcolor='#e5e7eb',
                range=[0, 100]
            ),
            height=400
        )
        
        # Add count labels above bars
        fig.update_traces(
            textposition='outside',
            texttemplate='%{text} students'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # By gender
    gender_data = df[df['gender'].notna()]
    if not gender_data.empty and len(gender_data['gender'].unique()) > 1:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        gender_stats = gender_data.groupby('gender')['attendance_rate'].agg(['mean', 'count']).reset_index()
        gender_stats.columns = ['Gender', 'Average Attendance Rate', 'Count']
        
        fig = px.bar(
            gender_stats,
            x='Gender',
            y='Average Attendance Rate',
            text='Count',
            title='Average Attendance Rate by Gender',
            labels={'Count': 'Number of Students'},
            color_discrete_sequence=['#2563eb']
        )
        
        fig.update_layout(
            title={
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white',
            yaxis=dict(
                gridcolor='#e5e7eb',
                range=[0, 100]
            ),
            height=400
        )
        
        # Add count labels above bars
        fig.update_traces(
            textposition='outside',
            texttemplate='%{text} students'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # By race
    race_data = df[df['race'].notna()]
    if not race_data.empty and len(race_data['race'].unique()) > 1:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        race_stats = race_data.groupby('race')['attendance_rate'].agg(['mean', 'count']).reset_index()
        race_stats.columns = ['Race/Ethnicity', 'Average Attendance Rate', 'Count']
        
        fig = px.bar(
            race_stats,
            x='Race/Ethnicity',
            y='Average Attendance Rate',
            text='Count',
            title='Average Attendance Rate by Race/Ethnicity',
            labels={'Count': 'Number of Students'},
            color_discrete_sequence=['#2563eb']
        )
        
        fig.update_layout(
            title={
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white',
            yaxis=dict(
                gridcolor='#e5e7eb',
                range=[0, 100]
            ),
            height=400
        )
        
        # Add count labels above bars
        fig.update_traces(
            textposition='outside',
            texttemplate='%{text} students'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

def show_interventions():
    st.header("Student Interventions")
    
    # Get student list
    session = get_session()
    students = session.query(Student).all()
    student_names = [f"{s.first_name} {s.last_name}" for s in students]
    
    # Student selection
    selected_student = st.selectbox("Select Student", student_names)
    if selected_student:
        student = students[student_names.index(selected_student)]
        
        # Show student info
        st.subheader("Student Information")
        
        # Calculate attendance rate and determine status color
        attendance_rate = calculate_attendance_rate(student.id)
        if attendance_rate < 80:
            status_color = '#fef2f2'
            text_color = '#dc2626'
            status_text = '⚠️ Chronic Absenteeism'
        elif attendance_rate < 85:
            status_color = '#fef3c7'
            text_color = '#d97706'
            status_text = '⚠️ At Risk'
        else:
            status_color = '#ecfdf5'
            text_color = '#059669'
            status_text = '✅ On Track'
        
        # Display student info in a styled card
        st.markdown(
            f"""<div style='padding: 1rem; border-radius: 0.5rem; background-color: {status_color}; margin-bottom: 1rem;'>
                <div style='display: flex; flex-direction: column; gap: 0.75rem; font-family: "Source Sans Pro", sans-serif;'>
                    <div style='color: {text_color};'>{student.first_name} {student.last_name}</div>
                    <div style='color: {text_color};'>Grade {student.grade}</div>
                    <div style='color: {text_color};'>{attendance_rate:.1f}%</div>
                    <div style='color: {text_color};'>{status_text}</div>
                </div>
            </div>""",
            unsafe_allow_html=True
        )
        
        # Show existing interventions
        st.subheader("Current Interventions")
        interventions = session.query(Intervention).filter_by(student_id=student.id).all()
        
        for intervention in interventions:
            with st.expander(f"{intervention.intervention_type} - {'Ongoing' if intervention.is_ongoing else 'Completed'}"):
                st.write(f"Start Date: {intervention.start_date}")
                if not intervention.is_ongoing and intervention.end_date:
                    st.write(f"End Date: {intervention.end_date}")
                st.write(f"Notes: {intervention.notes}")
        
        # Add new intervention
        st.subheader("Add New Intervention")
        with st.form(key="new_intervention_form"):
            # Intervention type selection
            intervention_type_options = [
                "Point Person",
                "Home Visits",
                "Morning Phone Call",
                "Buddy System",
                "Convos with Parents",
                "Social Worker Weekly Attendance Meeting",
                "Celebration",
                "Family Meetings",
                "Letters",
                "Incentivizes",
                "Family trips",
                "Individual Point Sheets For Attendance",
                "Attendance Contracts",
                "Lobby",
                "Other"
            ]
            
            selected_type = st.selectbox(
                "Intervention Type",
                intervention_type_options,
                key="intervention_type_select"
            )
            
            # Show text input for "Other" option
            final_intervention_type = selected_type
            if selected_type == "Other":
                other_type = st.text_input("Please specify the intervention type", key="other_type_input")
                if other_type:
                    final_intervention_type = other_type
                    
            # Start date
            start_date = st.date_input("Start Date", datetime.now(), key="intervention_start_date")
            
            # Status selection
            intervention_status = st.radio(
                "Intervention Status",
                options=["Ongoing", "Completed"],
                horizontal=True,
                key="intervention_status"
            )
            
            # End date field appears when Completed is selected
            end_date = None
            if intervention_status == "Completed":
                end_date = st.date_input(
                    "End Date",
                    value=start_date,  # Default to start date
                    min_value=start_date,  # Cannot be before start date
                    max_value=datetime.now().date(),  # Cannot be in the future
                    help="Must be after the start date and not in the future",
                    key="intervention_end_date"
                )
            else:
                end_date = None
            
            # Set is_ongoing based on status
            is_ongoing = (intervention_status == "Ongoing")
            
            # Notes field
            notes = st.text_area("Notes", key="notes")
            
            # Submit button
            if st.form_submit_button("Add Intervention"):
                try:
                    # Validate that if "Other" is selected, a custom type was provided
                    if selected_type == "Other" and not other_type:
                        st.error("Please specify the intervention type for 'Other'")
                        return
                        
                    # Validate dates
                    if intervention_status == "Completed" and end_date and end_date < start_date:
                        st.error("End date must be after start date")
                        return
                        
                    # Add intervention to database
                    new_intervention = Intervention(
                        student_id=student.id,
                        intervention_type=final_intervention_type,
                        start_date=start_date,
                        end_date=end_date,  # This will be None for ongoing interventions
                        is_ongoing=(intervention_status == "Ongoing"),
                        notes=notes if notes else None
                    )
                    
                    session.add(new_intervention)
                    session.commit()
                    st.success("Intervention added successfully!")
                    st.rerun()  # Refresh to show the new intervention
                    
                except Exception as e:
                    st.error(f"Error adding intervention: {str(e)}")
                    session.rollback()
                finally:
                    session.close()

if __name__ == "__main__":
    main()
