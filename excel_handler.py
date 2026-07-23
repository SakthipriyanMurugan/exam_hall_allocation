import pandas as pd
import io
from models import get_all_students, get_all_allocations, get_or_create_department, add_student, update_student, get_db_connection

def import_students_from_excel(file_stream, filename):
    """
    Imports student records from uploaded CSV or Excel file.
    Expected Columns: RegNo, Name, Department, Year, Semester, Email (or email id)
    """
    if filename.endswith('.csv'):
        df = pd.read_csv(file_stream)
    else:
        df = pd.read_excel(file_stream)

    # Normalize column names
    col_map = {}
    for col in df.columns:
        c_clean = str(col).strip().lower().replace(' ', '').replace('_', '').replace('id', '')
        if 'reg' in c_clean or 'roll' in c_clean:
            col_map[col] = 'reg_no'
        elif 'name' in c_clean:
            col_map[col] = 'name'
        elif 'dept' in c_clean or 'branch' in c_clean or 'department' in c_clean:
            col_map[col] = 'department'
        elif 'year' in c_clean:
            col_map[col] = 'year'
        elif 'sem' in c_clean:
            col_map[col] = 'semester'
        elif 'mail' in c_clean:
            col_map[col] = 'email'

    df.rename(columns=col_map, inplace=True)

    required_cols = ['reg_no', 'name', 'department', 'year', 'semester']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return {'status': 'error', 'message': f"Missing required columns in file: {', '.join(missing)}"}

    if 'email' not in df.columns:
        df['email'] = 'student@example.com'

    imported_count = 0
    updated_count = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    for idx, row in df.iterrows():
        reg_no = str(row['reg_no']).strip()
        name = str(row['name']).strip()
        dept_code = str(row['department']).strip().upper()
        
        try:
            year = int(row['year'])
            semester = int(row['semester'])
        except (ValueError, TypeError):
            year = 1
            semester = 1

        email = str(row['email']).strip() if pd.notna(row['email']) else f"{reg_no.lower()}@student.edu"

        if not reg_no or not name:
            continue

        dept_id = get_or_create_department(dept_code)

        # Check if student exists
        cursor.execute("SELECT id FROM students WHERE UPPER(reg_no) = UPPER(?)", (reg_no,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                "UPDATE students SET name=?, dept_id=?, year=?, semester=?, email=? WHERE id=?",
                (name, dept_id, year, semester, email, existing['id'])
            )
            updated_count += 1
        else:
            cursor.execute(
                "INSERT INTO students (reg_no, name, dept_id, year, semester, email) VALUES (?, ?, ?, ?, ?, ?)",
                (reg_no, name, dept_id, year, semester, email)
            )
            imported_count += 1

    conn.commit()
    conn.close()

    return {
        'status': 'success',
        'imported': imported_count,
        'updated': updated_count,
        'total': imported_count + updated_count
    }

def export_students_to_excel():
    """
    Exports full student master list with seating allocation details to an Excel file.
    """
    students = get_all_students()
    allocations = get_all_allocations()

    alloc_map = {a['student_id']: a for a in allocations}

    data = []
    for s in students:
        alloc = alloc_map.get(s['id'])
        data.append({
            'Register Number': s['reg_no'],
            'Student Name': s['name'],
            'Department Code': s['dept_code'] or 'N/A',
            'Department Name': s['dept_name'] or 'N/A',
            'Year': s['year'],
            'Semester': s['semester'],
            'Email Address': s['email'],
            'Absent Status': 'Absent' if s['is_absent'] else 'Present',
            'Allocated Hall': alloc['hall_name'] if alloc else 'Unallocated',
            'Bench Row': alloc['bench_row'] if alloc else '-',
            'Bench Column': alloc['bench_col'] if alloc else '-',
            'Seat Number': alloc['seat_position'] if alloc else '-',
            'Subject Code': alloc['subject_code'] if alloc else '-'
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Students & Seating')
    output.seek(0)

    return output
