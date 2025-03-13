
from app import app, db
import sqlite3
import os

# Comprehensive script to fix the media table structure

with app.app_context():
    db_path = os.path.join(app.instance_path, "school.db")
    print(f"Checking and fixing database at: {db_path}")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("Media table doesn't exist! Creating it...")
            cursor.execute("""
            CREATE TABLE media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                media_type VARCHAR(50) NOT NULL,
                file_url VARCHAR(255) NOT NULL,
                thumbnail_url VARCHAR(255),
                gallery_category VARCHAR(50),
                is_featured BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                video_platform VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
            print("Media table created successfully!")
        else:
            # Check existing columns
            cursor.execute("PRAGMA table_info(media)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add missing columns
            missing_columns = []
            if 'is_active' not in column_names:
                missing_columns.append(("is_active", "BOOLEAN DEFAULT TRUE"))
            if 'video_platform' not in column_names:
                missing_columns.append(("video_platform", "VARCHAR(50)"))
            
            for col_name, col_type in missing_columns:
                print(f"Adding {col_name} column to media table...")
                cursor.execute(f"ALTER TABLE media ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"Column {col_name} added successfully!")
            
            if not missing_columns:
                print("All required columns already exist in the media table.")
        
        conn.close()
        print("Database verification and fixes completed successfully.")
    except Exception as e:
        print(f"Error fixing database: {str(e)}")
