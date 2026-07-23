import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'exam_system.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Admins Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Departments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL
        )
    ''')

    # Subjects Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_id INTEGER NOT NULL,
            subject_code TEXT UNIQUE NOT NULL,
            subject_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            FOREIGN KEY (dept_id) REFERENCES departments (id) ON DELETE CASCADE
        )
    ''')

    # Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            dept_id INTEGER,
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            email TEXT NOT NULL,
            is_absent INTEGER DEFAULT 0,
            FOREIGN KEY (dept_id) REFERENCES departments (id) ON DELETE SET NULL
        )
    ''')

    # Halls Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS halls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hall_name TEXT UNIQUE NOT NULL,
            rows INTEGER DEFAULT 5,
            cols INTEGER DEFAULT 3,
            capacity_per_bench INTEGER DEFAULT 3,
            total_capacity INTEGER NOT NULL
        )
    ''')

    # Allocations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER UNIQUE NOT NULL,
            hall_id INTEGER NOT NULL,
            bench_row INTEGER NOT NULL,
            bench_col INTEGER NOT NULL,
            seat_position INTEGER NOT NULL,
            subject_id INTEGER,
            allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (hall_id) REFERENCES halls (id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE SET NULL
        )
    ''')

    # Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            allocation_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Present',
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (allocation_id) REFERENCES allocations (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        )
    ''')

    # Settings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    conn.commit()

    # Seed Default Admin Credentials (sakthi / sakthi2007)
    cursor.execute("SELECT * FROM admins WHERE username = 'sakthi'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admins (username, password) VALUES ('sakthi', 'sakthi2007')")

    # Seed Default Settings
    default_settings = {
        'sender_email': 'sakthipriyan1212@gmail.com',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': '587',
        'smtp_password': '',
        'simulation_mode': 'true'
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Seed Initial Demo Departments & Halls if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM departments")
    if cursor.fetchone()['cnt'] == 0:
        depts = [
            ('Computer Science & Engineering', 'CSE'),
            ('Electronics & Communication Engg', 'ECE'),
            ('Electrical & Electronics Engg', 'EEE'),
            ('Mechanical Engineering', 'MECH'),
            ('Civil Engineering', 'CIVIL')
        ]
        cursor.executemany("INSERT INTO departments (name, code) VALUES (?, ?)", depts)

    cursor.execute("SELECT COUNT(*) as cnt FROM halls")
    if cursor.fetchone()['cnt'] == 0:
        halls = [
            ('Exam Hall 101', 5, 3, 3, 45),
            ('Exam Hall 102', 5, 3, 3, 45),
            ('Exam Hall 103', 5, 3, 2, 30)
        ]
        cursor.executemany("INSERT INTO halls (hall_name, rows, cols, capacity_per_bench, total_capacity) VALUES (?, ?, ?, ?, ?)", halls)

    conn.commit()

    # Seed Demo Students if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM students")
    if cursor.fetchone()['cnt'] == 0:
        cursor.execute("SELECT id, code FROM departments")
        dept_map = {row['code']: row['id'] for row in cursor.fetchall()}

        cse = dept_map.get('CSE')
        ece = dept_map.get('ECE')
        eee = dept_map.get('EEE')
        mech = dept_map.get('MECH')

        # Add Subjects
        subjects = [
            (cse, 'CS8591', 'Computer Networks', 3, 5),
            (ece, 'EC8501', 'Digital Communication', 3, 5),
            (eee, 'EE8502', 'Power Electronics', 3, 5),
            (mech, 'ME8592', 'Thermal Engineering', 3, 5)
        ]
        for dept_id, code, name, yr, sem in subjects:
            cursor.execute(
                "INSERT OR IGNORE INTO subjects (dept_id, subject_code, subject_name, year, semester) VALUES (?, ?, ?, ?, ?)",
                (dept_id, code, name, yr, sem)
            )

        sample_students = [
            # CSE
            ('1001', 'Arun', cse, 3, 5, 'arun@gmail.com'),
            ('1002', 'Bala', cse, 3, 5, 'bala@gmail.com'),
            ('1003', 'Charan', cse, 3, 5, 'charan@gmail.com'),
            ('1004', 'Divya', cse, 3, 5, 'divya@gmail.com'),
            ('1005', 'Elan', cse, 3, 5, 'elan@gmail.com'),
            # ECE
            ('2001', 'Priya', ece, 3, 5, 'priya@gmail.com'),
            ('2002', 'Qadir', ece, 3, 5, 'qadir@gmail.com'),
            ('2003', 'Rahul', ece, 3, 5, 'rahul@gmail.com'),
            ('2004', 'Surya', ece, 3, 5, 'surya@gmail.com'),
            ('2005', 'Tamil', ece, 3, 5, 'tamil@gmail.com'),
            # EEE
            ('3001', 'Ezhil', eee, 3, 5, 'ezhil@gmail.com'),
            ('3002', 'Ganesh', eee, 3, 5, 'ganesh@gmail.com'),
            ('3003', 'Hema', eee, 3, 5, 'hema@gmail.com'),
            ('3004', 'Ishwarya', eee, 3, 5, 'ishwarya@gmail.com'),
            ('3005', 'Janani', eee, 3, 5, 'janani@gmail.com'),
            # MECH
            ('4001', 'Vasudevan', mech, 3, 5, 'vasu@gmail.com'),
            ('4002', 'Vikram', mech, 3, 5, 'vikram@gmail.com'),
            ('4003', 'Vimal', mech, 3, 5, 'vimal@gmail.com'),
            ('4004', 'Vishnu', mech, 3, 5, 'vishnu@gmail.com'),
            ('4005', 'Yamini', mech, 3, 5, 'yamini@gmail.com'),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO students (reg_no, name, dept_id, year, semester, email) VALUES (?, ?, ?, ?, ?, ?)",
            sample_students
        )
        conn.commit()

    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized & seeded successfully!")
