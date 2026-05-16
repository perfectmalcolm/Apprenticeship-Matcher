import sqlite3
import os

DB_FILE = "/tmp/jua_kali.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Table for Youth/Apprentices
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS youth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE,
            trade_interest TEXT,
            location TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table for Masters
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS masters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            trade TEXT,
            location TEXT,
            audio_url TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed Data for Demo
    cursor.execute("INSERT OR IGNORE INTO youth (phone_number, trade_interest, location) VALUES ('+254700000001', 'Carpentry', 'Nairobi')")
    cursor.execute("INSERT OR IGNORE INTO youth (phone_number, trade_interest, location) VALUES ('+254700000002', 'Welding', 'Mombasa')")
    cursor.execute("INSERT OR IGNORE INTO youth (phone_number, trade_interest, location) VALUES ('+254700000003', 'Plumbing', 'Nairobi')")
    
    conn.commit()
    conn.close()

def register_youth(phone_number: str, trade_interest: str, location: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO youth (phone_number, trade_interest, location) VALUES (?, ?, ?)",
            (phone_number, trade_interest, location)
        )
        conn.commit()
    finally:
        conn.close()

def save_master(phone_number: str, trade: str, location: str, audio_url: str, summary: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO masters (phone_number, trade, location, audio_url, summary) VALUES (?, ?, ?, ?, ?)",
        (phone_number, trade, location, audio_url, summary)
    )
    conn.commit()
    conn.close()

def search_apprentices_in_db(trade: str, location: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT phone_number FROM youth WHERE trade_interest LIKE ? AND location LIKE ?",
        (f"%{trade}%", f"%{location}%")
    )
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

def get_all_youth():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM youth ORDER BY registered_at DESC")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_all_masters():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM masters ORDER BY created_at DESC")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

# Initialize on import
init_db()
