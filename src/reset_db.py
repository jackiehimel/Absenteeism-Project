import os
from database import init_db

def reset_database():
    """Reset the database by deleting the existing file and reinitializing"""
    db_file = 'attendance.db'
    
    # Remove existing database
    if os.path.exists(db_file):
        print(f"Removing existing database: {db_file}")
        os.remove(db_file)
    
    # Initialize new database
    print("Initializing new database...")
    init_db()
    print("Database reset complete!")

if __name__ == '__main__':
    reset_database()
