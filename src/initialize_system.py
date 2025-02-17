import os
from database import init_db
from data_import import import_all_data

def initialize_system():
    """Initialize the entire system by:
    1. Creating the database and tables
    2. Importing all data from Excel/Numbers files
    """
    print("Step 1: Initializing database...")
    init_db()
    print("Database initialized successfully!")
    
    print("\nStep 2: Importing attendance data...")
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    import_all_data(data_dir)
    print("Data import completed!")

if __name__ == "__main__":
    initialize_system()
