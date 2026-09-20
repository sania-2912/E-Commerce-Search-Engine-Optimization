"""SQLite writer for product metadata and captions"""
import sqlite3
from typing import List, Optional
from Indexing_Pipeline.utils.logger import setup_logger

logger = setup_logger(__name__)

class SQLiteWriter:
    def __init__(self, db_path: str, table_name: str = "products"):
        self.db_path = db_path
        self.table_name = table_name
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to SQLite DB: {self.db_path}")

    def insert_product(self, pid: str, image_path: str, product_name: str,
                       main_category: str, brand: str, retail_price: float,
                       discounted_price: float, raw_caption: str,
                       norm_text: str) -> Optional[int]:
        try:
            query = f"""
                INSERT INTO {self.table_name}
                    (pid, image_path, product_name, main_category, brand,
                     retail_price, discounted_price, raw_caption, norm_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (
                pid, image_path, product_name, main_category, brand,
                retail_price, discounted_price, raw_caption, norm_text
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Insert error: {e}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()
