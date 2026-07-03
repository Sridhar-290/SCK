import sqlite3



def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Drop tables for fresh setup in demo
    # Create tables (Persistence ensured by using CREATE TABLE IF NOT EXISTS)

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_role_id INTEGER,
        keyword TEXT NOT NULL,
        importance INTEGER,
        FOREIGN KEY (job_role_id) REFERENCES job_roles(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        job_role_id INTEGER,
        role_name TEXT,
        resume_text TEXT,
        score INTEGER,
        result_json TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (job_role_id) REFERENCES job_roles(id)
    )
    ''')

    # New Roles Data
    new_roles = [
        ('DevOps Engineer', 'Manages infrastructure, CI/CD pipelines, and cloud services for seamless deployment.'),
        ('Frontend Developer', 'Focuses on visual aesthetics and user interactions using modern web frameworks.'),
        ('Data Scientist', 'Uses advanced statistical methods and machine learning to predict trends and patterns.'),
        ('Product Manager', 'Oversees product development flow, strategy, and roadmap planning.'),
        ('Cyber Security Analyst', 'Protects systems and networks from digital attacks and ensures compliance.'),
        ('Backend Developer', 'Builds and maintains the server-side logic and database integration for web apps.'),
        ('Full Stack Developer', 'Proficient in both frontend and backend technologies to build complete websites.'),
        ('AI/ML Engineer', 'Designs and implements AI models, neural networks, and machine learning algorithms.')
    ]
    
    # Check and Insert Roles
    for name, desc in new_roles:
        cursor.execute('SELECT id FROM job_roles WHERE name = ?', (name,))
        if not cursor.fetchone():
            cursor.execute('INSERT INTO job_roles (name, description) VALUES (?, ?)', (name, desc))
            print(f"Added role: {name}")

    conn.commit()
    
    # Get all role IDs
    cursor.execute('SELECT id, name FROM job_roles')
    role_map = {name: id for id, name in cursor.fetchall()}

    # Keywords Data (Role Name, Keyword, Importance)
    # 3=Must, 2=Important, 1=Optional
    new_keywords = [
        # DevOps
        ('DevOps Engineer', 'AWS', 3), ('DevOps Engineer', 'Docker', 3), ('DevOps Engineer', 'Kubernetes', 3),
        ('DevOps Engineer', 'CI/CD', 3), ('DevOps Engineer', 'Linux', 3), ('DevOps Engineer', 'Jenkins', 2),
        ('DevOps Engineer', 'Terraform', 2), ('DevOps Engineer', 'Python', 2), ('DevOps Engineer', 'Bash', 2),
        
        # Frontend
        ('Frontend Developer', 'React', 3), ('Frontend Developer', 'JavaScript', 3), ('Frontend Developer', 'CSS', 3),
        ('Frontend Developer', 'HTML', 3), ('Frontend Developer', 'TypeScript', 2), ('Frontend Developer', 'Redux', 2),
        ('Frontend Developer', 'Git', 2), ('Frontend Developer', 'Tailwind', 1), ('Frontend Developer', 'Next.js', 1),

        # Data Scientist
        ('Data Scientist', 'Python', 3), ('Data Scientist', 'Machine Learning', 3), ('Data Scientist', 'SQL', 3),
        ('Data Scientist', 'Pandas', 3), ('Data Scientist', 'TensorFlow', 2), ('Data Scientist', 'PyTorch', 2),
        ('Data Scientist', 'Statistics', 2), ('Data Scientist', 'Deep Learning', 1),

        # Product Manager
        ('Product Manager', 'Agile', 3), ('Product Manager', 'Roadmapping', 3), ('Product Manager', 'User Stories', 3),
        ('Product Manager', 'Jira', 2), ('Product Manager', 'Communication', 3), ('Product Manager', 'Strategy', 2),
        ('Product Manager', 'Data Analysis', 2), ('Product Manager', 'UX', 1),

        # Cyber Security
        ('Cyber Security Analyst', 'Network Security', 3), ('Cyber Security Analyst', 'Firewalls', 3),
        ('Cyber Security Analyst', 'Python', 2), ('Cyber Security Analyst', 'Linux', 2),
        ('Cyber Security Analyst', 'Penetration Testing', 3), ('Cyber Security Analyst', 'SIEM', 2),
        ('Cyber Security Analyst', 'Cryptography', 1),
        
        # Backend
        ('Backend Developer', 'Node.js', 3), ('Backend Developer', 'Python', 3), ('Backend Developer', 'SQL', 3),
        ('Backend Developer', 'API Design', 3), ('Backend Developer', 'Redis', 2), ('Backend Developer', 'Express', 2),
        ('Backend Developer', 'MongoDB', 2),
        
        # Full Stack
        ('Full Stack Developer', 'React', 3), ('Full Stack Developer', 'Node.js', 3), ('Full Stack Developer', 'SQL', 3),
        ('Full Stack Developer', 'System Architecture', 2), ('Full Stack Developer', 'Testing', 2), ('Full Stack Developer', 'JavaScript', 3),
        
        # AI/ML
        ('AI/ML Engineer', 'Python', 3), ('AI/ML Engineer', 'PyTorch', 3), ('AI/ML Engineer', 'TensorFlow', 3),
        ('AI/ML Engineer', 'Computer Vision', 2), ('AI/ML Engineer', 'NLP', 2), ('AI/ML Engineer', 'Linear Algebra', 3)
    ]

    for role_name, kw, imp in new_keywords:
        if role_name in role_map:
            role_id = role_map[role_name]
            cursor.execute('SELECT id FROM keywords WHERE job_role_id = ? AND keyword = ?', (role_id, kw))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO keywords (job_role_id, keyword, importance) VALUES (?, ?, ?)', (role_id, kw, imp))

    conn.commit()
    conn.close()
    print("Database expanded successfully.")

if __name__ == '__main__':
    init_db()
