
from app import app, db
import sqlite3
import os

# Run this script to add the is_active column to the gallery_item table

with app.app_context():
    db_path = os.path.join(app.instance_path, "school.db")
    print(f"Updating database at: {db_path}")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(gallery_item)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'is_active' not in column_names:
            print("Adding is_active column to gallery_item table...")
            cursor.execute("ALTER TABLE gallery_item ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            conn.commit()
            print("Column added successfully!")
        else:
            print("is_active column already exists.")
        
        conn.close()
        print("Database update completed.")
    except Exception as e:
        print(f"Error updating database: {str(e)}")
