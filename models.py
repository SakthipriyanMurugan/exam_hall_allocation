from database import get_db_connection

# --- Admin ---
def verify_admin(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
    admin = cursor.fetchone()
    conn.close()
    return admin

# --- Departments ---
def get_all_departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, COUNT(s.id) as student_count 
        FROM departments d 
        LEFT JOIN students s ON d.id = s.dept_id 
        GROUP BY d.id 
        ORDER BY d.name
    """)
    depts = cursor.fetchall()
    conn.close()
    return depts

def add_department(name, code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO departments (name, code) VALUES (?, ?)", (name, code))
    conn.commit()
    conn.close()

def delete_department(dept_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
    conn.commit()
    conn.close()

def get_or_create_department(code, name=None):
    code = code.strip().upper()
    if not name:
        name = f"{code} Department"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM departments WHERE UPPER(code) = ?", (code,))
    row = cursor.fetchone()
    if row:
        dept_id = row['id']
    else:
        cursor.execute("INSERT INTO departments (name, code) VALUES (?, ?)", (name, code))
        conn.commit()
        dept_id = cursor.lastrowid
    conn.close()
    return dept_id

# --- Subjects ---
def get_all_subjects(dept_id=None, year=None, semester=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.*, d.name as dept_name, d.code as dept_code 
        FROM subjects s 
        JOIN departments d ON s.dept_id = d.id
        WHERE 1=1
    """
    params = []
    if dept_id:
        query += " AND s.dept_id = ?"
        params.append(dept_id)
    if year:
        query += " AND s.year = ?"
        params.append(year)
    if semester:
        query += " AND s.semester = ?"
        params.append(semester)

    query += " ORDER BY s.subject_code"
    cursor.execute(query, params)
    subjects = cursor.fetchall()
    conn.close()
    return subjects

def add_subject(dept_id, subject_code, subject_name, year, semester):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subjects (dept_id, subject_code, subject_name, year, semester) VALUES (?, ?, ?, ?, ?)",
        (dept_id, subject_code, subject_name, year, semester)
    )
    conn.commit()
    conn.close()

def delete_subject(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()

# --- Students ---
def get_all_students(dept_id=None, year=None, semester=None, search=None, is_absent=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT st.*, d.name as dept_name, d.code as dept_code 
        FROM students st 
        LEFT JOIN departments d ON st.dept_id = d.id 
        WHERE 1=1
    """
    params = []
    if dept_id:
        query += " AND st.dept_id = ?"
        params.append(dept_id)
    if year:
        query += " AND st.year = ?"
        params.append(year)
    if semester:
        query += " AND st.semester = ?"
        params.append(semester)
    if is_absent is not None:
        query += " AND st.is_absent = ?"
        params.append(is_absent)
    if search:
        query += " AND (st.reg_no LIKE ? OR st.name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY st.reg_no"
    cursor.execute(query, params)
    students = cursor.fetchall()
    conn.close()
    return students

def get_student_by_id(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT st.*, d.name as dept_name, d.code as dept_code 
        FROM students st 
        LEFT JOIN departments d ON st.dept_id = d.id 
        WHERE st.id = ?
    """, (student_id,))
    student = cursor.fetchone()
    conn.close()
    return student

def get_student_by_regno_and_name(reg_no, name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT st.*, d.name as dept_name, d.code as dept_code 
        FROM students st 
        LEFT JOIN departments d ON st.dept_id = d.id 
        WHERE LOWER(TRIM(st.reg_no)) = LOWER(TRIM(?)) 
          AND LOWER(TRIM(st.name)) = LOWER(TRIM(?))
    """, (reg_no, name))
    student = cursor.fetchone()
    conn.close()
    return student

def add_student(reg_no, name, dept_id, year, semester, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (reg_no, name, dept_id, year, semester, email) VALUES (?, ?, ?, ?, ?, ?)",
        (reg_no, name, dept_id, year, semester, email)
    )
    conn.commit()
    conn.close()

def update_student(student_id, reg_no, name, dept_id, year, semester, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET reg_no=?, name=?, dept_id=?, year=?, semester=?, email=? WHERE id=?",
        (reg_no, name, dept_id, year, semester, email, student_id)
    )
    conn.commit()
    conn.close()

def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

def delete_multiple_students(student_ids):
    if not student_ids:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ', '.join(['?'] * len(student_ids))
    cursor.execute(f"DELETE FROM students WHERE id IN ({placeholders})", student_ids)
    conn.commit()
    conn.close()

def delete_all_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM allocations")
    cursor.execute("DELETE FROM students")
    conn.commit()
    conn.close()

def toggle_student_absent(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET is_absent = CASE WHEN is_absent = 1 THEN 0 ELSE 1 END WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

# --- Halls ---
def get_all_halls():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.*, 
               COUNT(a.id) as allocated_seats,
               (h.total_capacity - COUNT(a.id)) as empty_seats,
               ROUND(CAST(COUNT(a.id) AS FLOAT) / h.total_capacity * 100, 1) as utilization_pct
        FROM halls h 
        LEFT JOIN allocations a ON h.id = a.hall_id 
        GROUP BY h.id 
        ORDER BY h.hall_name
    """)
    halls = cursor.fetchall()
    conn.close()
    return halls

def add_hall(hall_name, rows, cols, capacity_per_bench):
    total_capacity = int(rows) * int(cols) * int(capacity_per_bench)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO halls (hall_name, rows, cols, capacity_per_bench, total_capacity) VALUES (?, ?, ?, ?, ?)",
        (hall_name, rows, cols, capacity_per_bench, total_capacity)
    )
    conn.commit()
    conn.close()

def update_hall(hall_id, hall_name, rows, cols, capacity_per_bench):
    total_capacity = int(rows) * int(cols) * int(capacity_per_bench)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE halls SET hall_name=?, rows=?, cols=?, capacity_per_bench=?, total_capacity=? WHERE id=?",
        (hall_name, rows, cols, capacity_per_bench, total_capacity, hall_id)
    )
    conn.commit()
    conn.close()

def delete_hall(hall_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM halls WHERE id = ?", (hall_id,))
    conn.commit()
    conn.close()

# --- Allocations ---
def get_all_allocations(hall_id=None, search=None, student_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT a.*, 
               st.reg_no, st.name as student_name, st.email, st.year, st.semester, st.is_absent,
               d.code as dept_code, d.name as dept_name,
               h.hall_name, h.rows as hall_rows, h.cols as hall_cols, h.capacity_per_bench,
               sub.subject_code, sub.subject_name
        FROM allocations a
        JOIN students st ON a.student_id = st.id
        LEFT JOIN departments d ON st.dept_id = d.id
        JOIN halls h ON a.hall_id = h.id
        LEFT JOIN subjects sub ON a.subject_id = sub.id
        WHERE 1=1
    """
    params = []
    if hall_id:
        query += " AND a.hall_id = ?"
        params.append(hall_id)
    if student_id:
        query += " AND a.student_id = ?"
        params.append(student_id)
    if search:
        query += " AND (st.reg_no LIKE ? OR st.name LIKE ? OR h.hall_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY h.hall_name, a.bench_col, a.bench_row, a.seat_position"
    cursor.execute(query, params)
    allocs = cursor.fetchall()
    conn.close()
    return allocs

def get_allocation_by_student_id(student_id):
    allocs = get_all_allocations(student_id=student_id)
    return allocs[0] if allocs else None

def clear_all_allocations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM allocations")
    conn.commit()
    conn.close()

def save_allocations(allocations_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM allocations")

    for item in allocations_list:
        cursor.execute("""
            INSERT INTO allocations (student_id, hall_id, bench_row, bench_col, seat_position, subject_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item['student_id'],
            item['hall_id'],
            item['bench_row'],
            item['bench_col'],
            item['seat_position'],
            item.get('subject_id')
        ))
        alloc_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO attendance (allocation_id, student_id, status)
            VALUES (?, ?, ?)
        """, (alloc_id, item['student_id'], 'Present'))

    conn.commit()
    conn.close()

# --- Dashboard Stats & Analytics ---
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM students WHERE is_absent = 1")
    absent_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM departments")
    total_departments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM halls")
    total_halls = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM allocations")
    total_allocations = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_capacity) FROM halls")
    total_capacity = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT d.code, COUNT(s.id) as count 
        FROM departments d 
        LEFT JOIN students s ON d.id = s.dept_id 
        GROUP BY d.id
    """)
    dept_dist = [{'code': row['code'], 'count': row['count']} for row in cursor.fetchall()]

    cursor.execute("""
        SELECT h.hall_name, h.total_capacity, COUNT(a.id) as used_seats 
        FROM halls h 
        LEFT JOIN allocations a ON h.id = a.hall_id 
        GROUP BY h.id
    """)
    hall_util = [{
        'name': row['hall_name'],
        'capacity': row['total_capacity'],
        'used': row['used_seats'],
        'empty': row['total_capacity'] - row['used_seats']
    } for row in cursor.fetchall()]

    cursor.execute("""
        SELECT sub.subject_code, sub.subject_name, COUNT(a.id) as count
        FROM allocations a
        JOIN subjects sub ON a.subject_id = sub.id
        GROUP BY sub.id
    """)
    subject_stats = [{'code': row['subject_code'], 'name': row['subject_name'], 'count': row['count']} for row in cursor.fetchall()]

    conn.close()

    return {
        'total_students': total_students,
        'absent_students': absent_students,
        'active_students': total_students - absent_students,
        'total_departments': total_departments,
        'total_halls': total_halls,
        'total_allocations': total_allocations,
        'total_capacity': total_capacity,
        'dept_dist': dept_dist,
        'hall_util': hall_util,
        'subject_stats': subject_stats
    }

# --- Settings ---
def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return settings

def update_settings(settings_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    for k, v in settings_dict.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()
