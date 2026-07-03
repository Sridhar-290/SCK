import sqlite3
import sys

def create_admin(email, full_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user:
            # Update existing user
            cursor.execute('UPDATE users SET is_admin = 1, full_name = ? WHERE email = ?', (full_name, email))
            print(f"Updated existing user {email} to Admin.")
        else:
            # Create new admin
            cursor.execute('INSERT INTO users (email, full_name, is_admin) VALUES (?, ?, 1)', (email, full_name))
            print(f"Created new Admin user: {email}")
            
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <email> <full_name>")
    else:
        create_admin(sys.argv[1], sys.argv[2])
