"""SQLite Database Reader for Product Metadata"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict

class SQLiteReader:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

    def get_product(self, pid: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE pid = ?", (pid,))
        row = cursor.fetchone()
        if not row:
            return None
        col_names = [d[0] for d in cursor.description]
        return dict(zip(col_names, row))

    def load_all_products(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM products", self.conn)

    def close(self):
        self.conn.close()
