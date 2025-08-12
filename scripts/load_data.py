import mysql.connector
import pandas as pd
from db_config import MYSQL_CONFIG
from logger_config import logger

class DataLoadError(Exception):

    pass

def load_csv_to_mysql():
    try:
        logger.info("Starting data load to MySQL...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM matches")
        cursor.execute("DELETE FROM deliveries")
        conn.commit()
        logger.info("Old data cleared from tables.")

        matches = pd.read_csv("matches.csv")
        matches.fillna("NA", inplace=True)
        for _, row in matches.iterrows():
            cursor.execute("""
                INSERT INTO matches VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(row))
        logger.info("Matches data loaded successfully.")

        deliveries = pd.read_csv("deliveries.csv")
        deliveries.fillna("NA", inplace=True)
        for _, row in deliveries.iterrows():
            cursor.execute("""
                INSERT INTO deliveries VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(row))
        logger.info("Deliveries data loaded successfully.")

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Data load completed successfully.")
    except Exception as e:
        logger.error(f"Error during data load: {e}")
        raise DataLoadError(f"Failed to load CSVs into MySQL: {e}")
