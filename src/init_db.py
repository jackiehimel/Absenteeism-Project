from database import Base, get_session

def init_database():
    # Get session which will create the engine
    session = get_session()
    
    # Create all tables
    Base.metadata.create_all(session.get_bind())
    print("Database tables created successfully!")
    
    # Close the session
    session.close()

if __name__ == "__main__":
    init_database()