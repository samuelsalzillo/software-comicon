import sqlite3
import time
from threading import Lock

__sqlite_lock = Lock()

def get_lock():
    global __sqlite_lock
    return __sqlite_lock

def execute_with_retry(cursor, query, params=(), retries=5, delay=0.1):
    """
    Executes a database query with retry logic to handle 'database is locked' errors.
    """
    for attempt in range(retries):
        try:
            cursor.execute(query, params)
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                if attempt < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise
            else:
                raise