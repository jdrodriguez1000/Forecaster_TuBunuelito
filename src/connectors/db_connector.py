import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

class DBConnector:
    def __init__(self):
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        
        self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        self.engine = create_engine(self.connection_string)

    def get_engine(self):
        return self.engine
