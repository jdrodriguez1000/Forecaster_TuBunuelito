import pandas as pd
from src.connectors.db_connector import DBConnector

class DataLoader:
    def __init__(self, config):
        self.config = config
        self.db = DBConnector()

    def load_data(self, table_name):
        """
        Carga datos desde Supabase.
        """
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, self.db.get_engine())
        return df
