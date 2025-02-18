import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from database import Student, AttendanceRecord, get_session
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
    
    # Get absolute path to data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    
    if student_count == 0:
        st.warning("No student data found in the database")
        if st.button("Import Data"):
            try:
                from data_import import import_all_data
                with st.spinner("Importing data..."):
                    st.write(f"Importing data from: {data_dir}")  # Debug info
                    import_all_data(data_dir)
                st.success("Data imported successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error importing data: {str(e)}")
                st.write("Debug info:", os.getcwd(), os.listdir())  # More debug info
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
        "Interventions"
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

def show_dashboard():
    # Get earliest and latest dates from the database
    session = get_session()
    earliest_date = session.query(AttendanceRecord.date).order_by(AttendanceRecord.date.asc()).first()
    latest_date = session.query(AttendanceRecord.date).order_by(AttendanceRecord.date.desc()).first()
    
    if earliest_date and latest_date:
        earliest_date = earliest_date[0]
        latest_date = latest_date[0]
    else:
        earliest_date = datetime(2018, 9, 1).date()
        latest_date = datetime(2025, 6, 19).date()
    
    # Custom CSS for date inputs and selectors
    st.markdown("""
        <style>
        [data-testid="stDateInput"] {
            width: 100%;
        }
        [data-testid="stDateInput"] > div {
            width: 100%;
        }
        [data-testid="stDateInput"] input {
            padding: 0.5rem;
            font-size: 1rem;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
        }
        .stSelectbox > div > div {
            padding: 0.5rem;
            font-size: 1rem;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Time period selector
    st.markdown("""
        <h3 style='margin: 1rem 0; color: #374151; font-size: 1.2rem; font-weight: 600;'>Time Period</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input(
            "Start Date",
            earliest_date,
            min_value=earliest_date,
            max_value=latest_date,
            key="start_date"
        )
        # Ensure start_date is a date object
        if isinstance(start_date, datetime):
            start_date = start_date.date()
    with col2:
        end_date = st.date_input(
            "End Date",
            latest_date,
            min_value=earliest_date,
            max_value=latest_date,
            key="end_date"
        )
        # Ensure end_date is a date object
        if isinstance(end_date, datetime):
            end_date = end_date.date()
    with col3:
        interval = st.selectbox(
            "Time Interval",
            ["Daily", "Weekly", "Monthly", "Yearly"],
            key="interval"
        )
    
    # Add some spacing before the grade tabs
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Get available grades
    available_grades = [grade[0] for grade in session.query(Student.grade).distinct().order_by(Student.grade)]
    
    # Create tabs for All Grades and individual grades
    tabs = ["All Grades"] + [f"Grade {g}" for g in available_grades]
    active_tab = st.tabs(tabs)
    
    for i, tab in enumerate(active_tab):
        with tab:
            try:
                # Convert grade to int for database query
                grade = None if i == 0 else int(available_grades[i-1])
                
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
            except Exception as e:
                st.error(f"Error loading attendance data: {str(e)}")
                continue
                
                # Add the main line
                fig.add_trace(go.Scatter(
                    x=trends['period'],
                    y=trends['attendance_rate'],
                    mode='lines+markers',
                    name='Attendance Rate',
                    line=dict(color='#2563eb', width=3),
                    marker=dict(size=8),
                    hovertemplate='%{x|%B %Y}<br>Attendance Rate: %{y:.1f}%<extra></extra>'
                ))
                
                # Add reference lines
                fig.add_hline(y=90, line_dash="dash", line_color="#22c55e", annotation_text="On Track (90%)", annotation_position="top right")
                fig.add_hline(y=85, line_dash="dash", line_color="#eab308", annotation_text="Warning (85%)", annotation_position="top right")
                fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", annotation_text="At Risk (80%)", annotation_position="top right")
                
                # Update layout
                fig.update_layout(
                    title={
                        'text': f'Attendance Trends {"(All Grades)" if grade is None else f"(Grade {grade})"}',
                        'y':0.95,
                        'x':0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    xaxis_title='Time Period',
                    yaxis_title='Attendance Rate (%)',
                    yaxis=dict(
                        range=[75, 100],
                        gridcolor='#e5e7eb',
                        zeroline=False
                    ),
                    xaxis=dict(
                        gridcolor='#e5e7eb',
                        type='date'
                    ),
                    plot_bgcolor='white',
                    showlegend=False,
                    height=500,
                    margin=dict(l=0, r=0, t=50, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No attendance data available for the selected time period.")
            
            # Get attendance trends
            start_date=start_date, 
            end_date=end_date, 
            interval=interval.lower()
            
            if trends.empty:
                st.info("No attendance data available for the selected criteria.")
                continue
            
            # Show attendance tiers
            tiers = get_tiered_attendance(grade=grade)
            if tiers:
                total_students = sum(len(tier) for tier in tiers.values())
                
                # Tier metrics in a container with a light background
                with st.container():
                    st.markdown("""
                        <div style='background-color: #f8fafc; padding: 1.5rem; border-radius: 8px; margin: 2rem 0;'>
                            <h3 style='margin: 0 0 1.5rem 0; color: #374151; font-size: 1.2rem;'>Attendance Tiers</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Custom CSS for tier boxes
                    st.markdown("""
                        <style>
                        [data-testid="stMetricValue"] {
                            font-size: 1.5rem !important;
                        }
                        .tier-box {
                            padding: 1rem;
                            border-radius: 8px;
                            text-align: center;
                            height: 100%;
                        }
                        .tier-box h4 {
                            font-size: 1.1rem;
                            margin-bottom: 0.5rem;
                            font-weight: 600;
                        }
                        .tier-box p {
                            font-size: 1rem;
                            margin: 0;
                            color: #4b5563;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    # Create tier boxes with better styling
                    tier_cols = st.columns(4)
                    
                    with tier_cols[0]:
                        chronic_count = len(tiers['tier3'])
                        st.markdown(f"""
                            <div class='tier-box' style='background-color: #fee2e2; border: 1px solid #fecaca;'>
                                <h4 style='color: #991b1b;'>Tier 3 (Chronic)</h4>
                                <p style='font-size: 1.3rem; color: #dc2626;'>{chronic_count} students</p>
                                <p>{chronic_count/total_students*100:.1f}%</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with tier_cols[1]:
                        at_risk_count = len(tiers['tier2'])
                        st.markdown(f"""
                            <div class='tier-box' style='background-color: #fef3c7; border: 1px solid #fde68a;'>
                                <h4 style='color: #92400e;'>Tier 2 (At Risk)</h4>
                                <p style='font-size: 1.3rem; color: #d97706;'>{at_risk_count} students</p>
                                <p>{at_risk_count/total_students*100:.1f}%</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with tier_cols[2]:
                        warning_count = len(tiers['tier1'])
                        st.markdown(f"""
                            <div class='tier-box' style='background-color: #dbeafe; border: 1px solid #bfdbfe;'>
                                <h4 style='color: #1e40af;'>Tier 1 (Warning)</h4>
                                <p style='font-size: 1.3rem; color: #2563eb;'>{warning_count} students</p>
                                <p>{warning_count/total_students*100:.1f}%</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with tier_cols[3]:
                        on_track_count = len(tiers['on_track'])
                        st.markdown(f"""
                            <div class='tier-box' style='background-color: #dcfce7; border: 1px solid #bbf7d0;'>
                                <h4 style='color: #166534;'>On Track</h4>
                                <p style='font-size: 1.3rem; color: #16a34a;'>{on_track_count} students</p>
                                <p>{on_track_count/total_students*100:.1f}%</p>
                            </div>
                        """, unsafe_allow_html=True)
            
            # Attendance Trends section
            with st.container():
                st.markdown("""
                    <div style='background-color: #F9FAFB; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;'>
                        <h3 style='margin: 0 0 1rem 0; color: #374151;'>Attendance Trends</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                # Format period based on interval
                if interval == 'daily':
                    trends['display_period'] = trends['period'].dt.strftime('%Y-%m-%d')
                elif interval == 'weekly':
                    trends['display_period'] = trends['period'].dt.strftime('Week of %Y-%m-%d')
                elif interval == 'monthly':
                    trends['display_period'] = trends['period'].dt.strftime('%B %Y')
                else:  # yearly
                    trends['display_period'] = trends['period'].dt.strftime('%Y')
                
                # Calculate average attendance rate
                avg_rate = trends['attendance_rate'].mean()
                
                # Add summary metrics above the plot
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Average Rate", f"{avg_rate:.1f}%")
                with col2:
                    min_rate = trends['attendance_rate'].min()
                    st.metric("Lowest Rate", f"{min_rate:.1f}%")
                with col3:
                    max_rate = trends['attendance_rate'].max()
                    st.metric("Highest Rate", f"{max_rate:.1f}%")
                with col4:
                    current_rate = trends['attendance_rate'].iloc[-1]
                    delta = current_rate - trends['attendance_rate'].iloc[-2]
                    st.metric("Current Rate", f"{current_rate:.1f}%", f"{delta:+.1f}%")
                
                # Create a more informative plot
                fig = go.Figure()
                
                # Add the main attendance line with gradient color
                fig.add_trace(go.Scatter(
                    x=trends['display_period'],
                    y=trends['attendance_rate'],
                    mode='lines+markers',
                    line=dict(width=3, color='#2563eb'),
                    marker=dict(
                        size=8,
                        color=trends['attendance_rate'],
                        colorscale=[
                            [0, '#ef4444'],    # Red for low values
                            [0.5, '#eab308'],  # Yellow for middle values
                            [1, '#22c55e']     # Green for high values
                        ],
                        showscale=False
                    ),
                    hovertemplate='%{y:.1f}%<br>%{x}'
                ))
                
                # Add shaded regions for different tiers
                # Add shaded regions with more visible colors
                fig.add_hrect(y0=90, y1=100, fillcolor='rgba(34,197,94,0.15)', layer='below', line_width=0)  # Green
                fig.add_hrect(y0=85, y1=90, fillcolor='rgba(59,130,246,0.15)', layer='below', line_width=0)  # Blue
                fig.add_hrect(y0=80, y1=85, fillcolor='rgba(250,204,21,0.2)', layer='below', line_width=0)  # Brighter yellow
                fig.add_hrect(y0=75, y1=80, fillcolor='rgba(239,68,68,0.15)', layer='below', line_width=0)  # Red
                
                # Add reference lines with improved styling
                fig.add_hline(y=avg_rate, line_dash="dash", line_color="rgba(0,0,0,0.5)",
                             annotation=dict(
                                text=f"Average: {avg_rate:.1f}%",
                                font=dict(size=12, color='rgba(0,0,0,0.7)'),
                                bgcolor="rgba(255,255,255,0.9)",
                                bordercolor="rgba(0,0,0,0.1)",
                                borderwidth=1
                             ),
                             annotation_position="bottom right")
                
                # Add reference lines for attendance tiers
                annotations = [
                    dict(y=90, text="On Track (≥90%)", color="#22c55e"),
                    dict(y=85, text="Warning (<85%)", color="#3b82f6"),
                    dict(y=80, text="At Risk (<80%)", color="#ef4444")
                ]
                
                for ann in annotations:
                    fig.add_hline(
                        y=ann['y'],
                        line_dash="dot",
                        line_color=ann['color'],
                        line_width=1,
                        annotation=dict(
                            text=ann['text'],
                            font=dict(size=12, color=ann['color']),
                            bgcolor="rgba(255,255,255,0.9)",
                            bordercolor="rgba(0,0,0,0.1)",
                            borderwidth=1
                        ),
                        annotation_position="left"
                    )
                
                # Update layout with better styling and margins
                fig.update_layout(
                    title={
                        'text': 'Attendance Trends Over Time',
                        'font': {'size': 24, 'color': '#111827'},
                        'y': 0.95,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    margin=dict(t=80, b=50, l=100, r=40),  # Increased left margin significantly
                    xaxis_title={
                        'text': 'Time Period',
                        'font': {'size': 16, 'color': '#374151'},
                        'standoff': 20
                    },
                    yaxis_title={
                        'text': 'Attendance Rate (%)',
                        'font': {'size': 16, 'color': '#374151'},
                        'standoff': 30  # Increased standoff for y-axis title
                    },
                    yaxis_range=[75, 100],
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(0,0,0,0.1)',
                        tickangle=45,
                        tickfont=dict(size=14),
                        title_standoff=20
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(0,0,0,0.1)',
                        tickformat='.0f',
                        tickfont=dict(size=14),
                        title_standoff=20,
                        automargin=True  # Ensure y-axis labels are not cut off
                    ),
                    hoverlabel=dict(
                        bgcolor='white',
                        font_size=14,
                        bordercolor='rgba(0,0,0,0.1)'
                    ),
                    height=500  # Taller plot for better visibility
                )
                if interval != 'yearly':
                    fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Absence Patterns section
            with st.container():
                st.markdown("""
                    <div style='background-color: #F9FAFB; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;'>
                        <h3 style='margin: 0 0 1rem 0; color: #374151;'>Absence Patterns</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                patterns = analyze_absence_patterns(grade=grade)
                
                if patterns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Day of week patterns with improved visualization
                        fig = go.Figure()
                        
                        # Add bars with better styling
                        fig.add_trace(go.Bar(
                            x=patterns['day_of_week'].index,
                            y=patterns['day_of_week'].values,
                            text=patterns['day_of_week'].values.round(1).astype(str) + '%',
                            textposition='auto',
                            marker_color='#2563eb',
                            hovertemplate='%{x}<br>Absence Rate: %{y:.1f}%<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title={
                                'text': 'Absences by Day of Week',
                                'font': {'size': 20, 'color': '#111827'},
                                'y': 0.95,
                                'x': 0.5,
                                'xanchor': 'center',
                                'yanchor': 'top'
                            },
                            margin=dict(t=60, b=40, l=60, r=20),
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            showlegend=False,
                            xaxis=dict(
                                title={
                                    'text': 'Day of Week',
                                    'font': {'size': 14, 'color': '#374151'},
                                    'standoff': 20
                                },
                                showgrid=True,
                                gridwidth=1,
                                gridcolor='rgba(0,0,0,0.1)',
                                tickfont=dict(size=12)
                            ),
                            yaxis=dict(
                                title={
                                    'text': 'Absence Rate (%)',
                                    'font': {'size': 14, 'color': '#374151'},
                                    'standoff': 20
                                },
                                showgrid=True,
                                gridwidth=1,
                                gridcolor='rgba(0,0,0,0.1)',
                                tickfont=dict(size=12),
                                range=[0, max(patterns['day_of_week'].values) * 1.1]
                            ),
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Month patterns with improved visualization
                        fig = go.Figure()
                        
                        # Add bars with better styling
                        fig.add_trace(go.Bar(
                            x=patterns['month'].index,
                            y=patterns['month'].values,
                            text=patterns['month'].values.round(1).astype(str) + '%',
                            textposition='auto',
                            marker_color='#2563eb',
                            hovertemplate='%{x}<br>Absence Rate: %{y:.1f}%<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title={
                                'text': 'Absences by Month',
                                'font': {'size': 20, 'color': '#111827'},
                                'y': 0.95,
                                'x': 0.5,
                                'xanchor': 'center',
                                'yanchor': 'top'
                            },
                            margin=dict(t=60, b=40, l=60, r=20),
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            showlegend=False,
                            xaxis=dict(
                                title={
                                    'text': 'Month',
                                    'font': {'size': 14, 'color': '#374151'},
                                    'standoff': 20
                                },
                                showgrid=True,
                                gridwidth=1,
                                gridcolor='rgba(0,0,0,0.1)',
                                tickfont=dict(size=12)
                            ),
                            yaxis=dict(
                                title={
                                    'text': 'Absence Rate (%)',
                                    'font': {'size': 14, 'color': '#374151'},
                                    'standoff': 20
                                },
                                showgrid=True,
                                gridwidth=1,
                                gridcolor='rgba(0,0,0,0.1)',
                                tickfont=dict(size=12),
                                range=[0, max(patterns['month'].values) * 1.1]
                            ),
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Detailed Lists
            if st.checkbox("Show Detailed Student Lists", key=f"show_details_{i}"):
                st.subheader("Students by Tier")
                
                # Show tier 3 (chronic) students
                if tiers['tier3']:
                    st.error("Tier 3 - Chronic Absenteeism")
                    df = pd.DataFrame([
                        {
                            'Student ID': t['student'].id,
                            'Grade': t['student'].grade,
                            'Attendance Rate': f"{t['attendance_rate']:.1f}%",
                            'Last Updated': t['last_updated']
                        } for t in tiers['tier3']
                    ])
                    st.dataframe(df, hide_index=True)
                
                # Show tier 2 students
                if tiers['tier2']:
                    st.warning("Tier 2 - At Risk")
                    df = pd.DataFrame([
                        {
                            'Student ID': t['student'].id,
                            'Grade': t['student'].grade,
                            'Attendance Rate': f"{t['attendance_rate']:.1f}%",
                            'Last Updated': t['last_updated']
                        } for t in tiers['tier2']
                    ])
                    st.dataframe(df, hide_index=True)

def show_student_details():
    st.header("Student Details")
    
    # Get all students
    session = get_session()
    students = session.query(Student).order_by(Student.id).all()
    
    if not students:
        st.info("No students found in the database")
        return
    
    # Student selector in a styled container
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    student_ids = [s.id for s in students]
    student_id = st.selectbox("Select Student", student_ids, key="student_details_select")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if student_id:
        student = session.query(Student).get(student_id)
        
        # Student information section
        st.subheader("Student Information")
        
        # Main info card
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display student information
            st.markdown(f"""
                <div class='student-info'><strong>Name:</strong> {student.name}</div>
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
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Attendance History section
        st.subheader("Attendance History")
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)
        
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
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    grade = st.selectbox(
        "Select Grade", 
        [None] + available_grades, 
        format_func=lambda x: 'All Grades' if x is None else f'Grade {x}'
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Get tiered attendance data
    tiers = get_tiered_attendance(grade=grade)
    
    # Calculate total students and check if we have data
    total_students = sum(len(tier) for tier in tiers.values())
    if total_students == 0:
        st.warning("No attendance data available for the selected criteria")
        return
        
    # Show tier summary
    st.subheader("Attendance Tiers Summary")
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
    
    # Show detailed student lists
    st.subheader("Students Requiring Intervention")
    
    if tiers['tier3'] or tiers['tier2']:
        # Combine tier 3 and tier 2 students for analysis
        at_risk_students = tiers['tier3'] + tiers['tier2']
        
        # Create DataFrame for analysis
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
        
        # Show detailed tables by tier
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        if tiers['tier3']:
            st.markdown("<div class='status-card status-danger'>Tier 3 - Chronic Absenteeism (Below 80% Attendance)</div>", unsafe_allow_html=True)
            chronic_df = df[df['Tier'] == '3 (Chronic)'].copy()
            chronic_df['Attendance Rate'] = chronic_df['Attendance Rate'].apply(lambda x: f"{x:.1f}%")
            chronic_df['Last Updated'] = pd.to_datetime(chronic_df['Last Updated']).dt.strftime('%Y-%m-%d')
            st.dataframe(chronic_df.drop('Tier', axis=1), hide_index=True)
        
        if tiers['tier2']:
            st.markdown("<div class='status-card status-warning'>Tier 2 - At Risk (80-84.99% Attendance)</div>", unsafe_allow_html=True)
            at_risk_df = df[df['Tier'] == '2 (At Risk)'].copy()
            at_risk_df['Attendance Rate'] = at_risk_df['Attendance Rate'].apply(lambda x: f"{x:.1f}%")
            at_risk_df['Last Updated'] = pd.to_datetime(at_risk_df['Last Updated']).dt.strftime('%Y-%m-%d')
            st.dataframe(at_risk_df.drop('Tier', axis=1), hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.success("No students currently requiring immediate intervention.")

def show_demographics():
    st.header("Demographics Analysis")
    
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
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    grade = st.selectbox(
        "Select Grade", 
        [None] + available_grades, 
        format_func=lambda x: 'All Grades' if x is None else f'Grade {x}',
        key="demographics_grade_select"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
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
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
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
        grade_stats = grade_data.groupby('grade')['attendance_rate'].agg(['mean', 'count']).reset_index()
        grade_stats.columns = ['Grade', 'Average Attendance Rate', 'Count']
        
        fig = px.bar(
            grade_stats,
            x='Grade',
            y='Average Attendance Rate',
            text='Count',
            title='Average Attendance Rate by Grade',
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
    st.header("Interventions")
    
    # Student selector
    session = get_session()
    students = session.query(Student).order_by(Student.id).all()
    
    if not students:
        st.info("No students found in the database")
        return
    
    student_ids = [s.id for s in students]
    student_id = st.selectbox("Select Student", student_ids, key="interventions_student_select")
    
    if student_id:
        student = session.query(Student).get(student_id)
        
        # Show student info
        st.subheader("Student Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Name:", student.name)
            st.write("Grade:", student.grade)
        
        with col2:
            attendance_rate = calculate_attendance_rate(student.id)
            st.write(f"Attendance Rate: {attendance_rate:.1f}%")
            
            if attendance_rate < 80:
                st.error("⚠️ Chronic Absenteeism")
            elif attendance_rate < 90:
                st.warning("⚠️ At Risk")
        
        # Show interventions
        st.subheader("Intervention History")
        interventions = student.interventions
        
        if interventions:
            data = [{
                'Date': i.date,
                'Type': i.type,
                'Description': i.description,
                'Outcome': i.outcome
            } for i in interventions]
            
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.write("No interventions recorded")
        
        # Add new intervention
        st.subheader("Add Intervention")
        with st.form("new_intervention"):
            intervention_type = st.selectbox(
                "Type",
                ["Phone Call", "Meeting", "Letter", "Home Visit", "Other"]
            )
            description = st.text_area("Description")
            outcome = st.text_area("Outcome")
            submitted = st.form_submit_button("Add Intervention")
            
            if submitted:
                from database import Intervention
                
                intervention = Intervention(
                    student=student,
                    date=datetime.now().date(),
                    type=intervention_type,
                    description=description,
                    outcome=outcome
                )
                
                session.add(intervention)
                session.commit()
                st.success("Intervention added successfully!")
                st.experimental_rerun()

if __name__ == "__main__":
    main()
