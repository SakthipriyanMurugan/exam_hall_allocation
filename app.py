from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from functools import wraps
import os

from database import init_db
import models
from allocation_engine import run_seating_allocation
from pdf_generator import (
    generate_hall_seating_pdf,
    generate_student_master_pdf,
    generate_invigilator_pdf,
    generate_attendance_sheet_pdf
)
from excel_handler import import_students_from_excel, export_students_to_excel
from email_service import send_allocation_emails

app = Flask(__name__)
app.secret_key = 'exam_allocation_secret_key_sakthi_2007'

init_db()

# --- Access Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login as admin to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('student_id'):
            flash('Please login to access student portal.', 'warning')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin = models.verify_admin(username, password)
        if admin:
            session['admin_logged_in'] = True
            session['admin_username'] = admin['username']
            flash('Successfully logged in as Admin.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Admin ID or Password! Default: sakthi / sakthi2007', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# --- Student Portal ---
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        reg_no = request.form.get('reg_no', '').strip()
        name = request.form.get('name', '').strip()

        student = models.get_student_by_regno_and_name(reg_no, name)
        if student:
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            session['student_reg_no'] = student['reg_no']
            flash(f"Welcome {student['name']}!", 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('No matching student found. Please verify your Register Number and Name.', 'danger')

    return render_template('student_login.html')

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student_id = session.get('student_id')
    student = models.get_student_by_id(student_id)
    alloc = models.get_allocation_by_student_id(student_id)
    return render_template('student_dashboard.html', student=student, alloc=alloc)

@app.route('/student/logout')
def student_logout():
    session.pop('student_id', None)
    session.pop('student_name', None)
    session.pop('student_reg_no', None)
    flash('Logged out from student portal.', 'info')
    return redirect(url_for('student_login'))

# --- Admin Dashboard ---
@app.route('/')
@app.route('/dashboard')
@admin_required
def dashboard():
    stats = models.get_dashboard_stats()
    halls = models.get_all_halls()
    return render_template('dashboard.html', stats=stats, halls=halls)

# --- Students ---
@app.route('/students')
@admin_required
def students_view():
    dept_id = request.args.get('dept_id', type=int)
    year = request.args.get('year', type=int)
    semester = request.args.get('semester', type=int)
    search = request.args.get('search', type=str)

    students = models.get_all_students(dept_id=dept_id, year=year, semester=semester, search=search)
    departments = models.get_all_departments()

    return render_template('students.html', students=students, departments=departments, req_args=request.args)

@app.route('/students/add', methods=['POST'])
@admin_required
def add_student_route():
    reg_no = request.form.get('reg_no', '').strip()
    name = request.form.get('name', '').strip()
    dept_id = request.form.get('dept_id', type=int)
    year = request.form.get('year', type=int)
    semester = request.form.get('semester', type=int)
    email = request.form.get('email', '').strip()

    try:
        models.add_student(reg_no, name, dept_id, year, semester, email)
        flash(f'Student {name} added successfully.', 'success')
    except Exception as e:
        flash(f'Error adding student: {str(e)}', 'danger')

    return redirect(url_for('students_view'))

@app.route('/students/edit/<int:student_id>', methods=['POST'])
@admin_required
def edit_student_route(student_id):
    reg_no = request.form.get('reg_no', '').strip()
    name = request.form.get('name', '').strip()
    dept_id = request.form.get('dept_id', type=int)
    year = request.form.get('year', type=int)
    semester = request.form.get('semester', type=int)
    email = request.form.get('email', '').strip()

    try:
        models.update_student(student_id, reg_no, name, dept_id, year, semester, email)
        flash('Student record updated.', 'success')
    except Exception as e:
        flash(f'Error updating student: {str(e)}', 'danger')

    return redirect(url_for('students_view'))

@app.route('/students/delete/<int:student_id>', methods=['POST'])
@admin_required
def delete_student_route(student_id):
    models.delete_student(student_id)
    flash('Student deleted.', 'info')
    return redirect(url_for('students_view'))

@app.route('/students/delete-multiple', methods=['POST'])
@admin_required
def delete_multiple_students_route():
    student_ids = request.form.getlist('student_ids')
    if student_ids:
        models.delete_multiple_students(student_ids)
        flash(f'Successfully deleted {len(student_ids)} selected students.', 'info')
    else:
        flash('No students selected for deletion.', 'warning')
    return redirect(url_for('students_view'))

@app.route('/students/delete-all', methods=['POST'])
@admin_required
def delete_all_students_route():
    models.delete_all_students()
    flash('All student records and seating allocations have been permanently deleted.', 'info')
    return redirect(url_for('students_view'))

@app.route('/students/toggle-absent/<int:student_id>', methods=['POST'])
@admin_required
def toggle_absent_route(student_id):
    models.toggle_student_absent(student_id)
    flash('Student absent status updated.', 'info')
    return redirect(url_for('students_view'))

@app.route('/students/import', methods=['POST'])
@admin_required
def import_students_route():
    file = request.files.get('excel_file')
    if not file or file.filename == '':
        flash('No file selected for import.', 'danger')
        return redirect(url_for('students_view'))

    res = import_students_from_excel(file.stream, file.filename)
    if res['status'] == 'success':
        flash(f"Import successful! Added {res['imported']} new, updated {res['updated']} records.", 'success')
    else:
        flash(res['message'], 'danger')

    return redirect(url_for('students_view'))

@app.route('/students/export')
@admin_required
def export_students():
    excel_buf = export_students_to_excel()
    return send_file(
        excel_buf,
        as_attachment=True,
        download_name='Exam_Students_Allocation_List.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- Departments & Subjects ---
@app.route('/departments')
@admin_required
def departments_view():
    departments = models.get_all_departments()
    subjects = models.get_all_subjects()
    return render_template('departments.html', departments=departments, subjects=subjects)

@app.route('/departments/add', methods=['POST'])
@admin_required
def add_department_route():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    try:
        models.add_department(name, code)
        flash(f'Department {code} added.', 'success')
    except Exception as e:
        flash(f'Error adding department: {str(e)}', 'danger')

    return redirect(url_for('departments_view'))

@app.route('/departments/delete/<int:dept_id>', methods=['POST'])
@admin_required
def delete_department_route(dept_id):
    models.delete_department(dept_id)
    flash('Department deleted.', 'info')
    return redirect(url_for('departments_view'))

@app.route('/subjects/add', methods=['POST'])
@admin_required
def add_subject_route():
    dept_id = request.form.get('dept_id', type=int)
    subject_code = request.form.get('subject_code', '').strip().upper()
    subject_name = request.form.get('subject_name', '').strip()
    year = request.form.get('year', type=int)
    semester = request.form.get('semester', type=int)

    try:
        models.add_subject(dept_id, subject_code, subject_name, year, semester)
        flash(f'Subject {subject_code} added.', 'success')
    except Exception as e:
        flash(f'Error adding subject: {str(e)}', 'danger')

    return redirect(url_for('departments_view'))

@app.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@admin_required
def delete_subject_route(subject_id):
    models.delete_subject(subject_id)
    flash('Subject deleted.', 'info')
    return redirect(url_for('departments_view'))

# --- Halls ---
@app.route('/halls')
@admin_required
def halls_view():
    halls = models.get_all_halls()
    return render_template('halls.html', halls=halls)

@app.route('/halls/add', methods=['POST'])
@admin_required
def add_hall_route():
    hall_name = request.form.get('hall_name', '').strip()
    rows = request.form.get('rows', type=int, default=5)
    cols = request.form.get('cols', type=int, default=3)
    capacity_per_bench = request.form.get('capacity_per_bench', type=int, default=3)

    try:
        models.add_hall(hall_name, rows, cols, capacity_per_bench)
        flash(f'Hall {hall_name} added successfully.', 'success')
    except Exception as e:
        flash(f'Error creating hall: {str(e)}', 'danger')

    return redirect(url_for('halls_view'))

@app.route('/halls/edit/<int:hall_id>', methods=['POST'])
@admin_required
def edit_hall_route(hall_id):
    hall_name = request.form.get('hall_name', '').strip()
    rows = request.form.get('rows', type=int, default=5)
    cols = request.form.get('cols', type=int, default=3)
    capacity_per_bench = request.form.get('capacity_per_bench', type=int, default=3)

    try:
        models.update_hall(hall_id, hall_name, rows, cols, capacity_per_bench)
        flash('Hall record updated.', 'success')
    except Exception as e:
        flash(f'Error updating hall: {str(e)}', 'danger')

    return redirect(url_for('halls_view'))

@app.route('/halls/delete/<int:hall_id>', methods=['POST'])
@admin_required
def delete_hall_route(hall_id):
    models.delete_hall(hall_id)
    flash('Hall deleted.', 'info')
    return redirect(url_for('halls_view'))

# --- Seating Allocation Engine & Exam Mappings ---
@app.route('/allocation')
@admin_required
def allocation_view():
    allocations = models.get_all_allocations()
    settings = models.get_settings()
    departments = models.get_all_departments()
    subjects = models.get_all_subjects()

    if 'session_mappings' not in session:
        session['session_mappings'] = []

    return render_template(
        'allocation.html',
        allocations=allocations,
        settings=settings,
        departments=departments,
        subjects=subjects,
        session_mappings=session['session_mappings']
    )

@app.route('/allocation/add-mapping', methods=['POST'])
@admin_required
def add_mapping_route():
    dept_id = request.form.get('dept_id', type=int)
    year = request.form.get('year', type=int)
    semester = request.form.get('semester', type=int)
    subject_id = request.form.get('subject_id', type=int)

    if not dept_id or not year or not semester or not subject_id:
        flash('Please select Department, Year, Semester, and Subject.', 'danger')
        return redirect(url_for('allocation_view'))

    depts = {d['id']: d for d in models.get_all_departments()}
    subjs = {s['id']: s for s in models.get_all_subjects()}

    dept_info = depts.get(dept_id)
    subj_info = subjs.get(subject_id)

    mapping_entry = {
        'dept_id': dept_id,
        'dept_code': dept_info['code'] if dept_info else 'N/A',
        'dept_name': dept_info['name'] if dept_info else 'N/A',
        'year': year,
        'semester': semester,
        'subject_id': subject_id,
        'subject_code': subj_info['subject_code'] if subj_info else 'N/A',
        'subject_name': subj_info['subject_name'] if subj_info else 'N/A'
    }

    # Retrieve existing mappings
    existing_mappings = session.get('session_mappings', [])
    # Check for duplicate combination
    if any(m['dept_id'] == dept_id and m['year'] == year and m['semester'] == semester and m['subject_id'] == subject_id for m in existing_mappings):
        flash('This Department, Year, Semester, and Exam Subject combination has already been added.', 'danger')
        return redirect(url_for('allocation_view'))

    # Append new mapping
    mappings = list(existing_mappings)
    mappings.append(mapping_entry)
    session['session_mappings'] = mappings

    flash(f"Added {mapping_entry['dept_code']} (Year {year}, Sem {semester}) -> {mapping_entry['subject_code']} to Exam Session.", 'success')
    return redirect(url_for('allocation_view'))

@app.route('/allocation/remove-mapping/<int:idx>', methods=['POST'])
@admin_required
def remove_mapping_route(idx):
    if 'session_mappings' in session:
        mappings = list(session['session_mappings'])
        if 0 <= idx < len(mappings):
            removed = mappings.pop(idx)
            session['session_mappings'] = mappings
            flash(f"Removed {removed.get('dept_code')} exam mapping.", 'info')

    return redirect(url_for('allocation_view'))

@app.route('/allocation/clear-mappings', methods=['POST'])
@admin_required
def clear_mappings_route():
    session['session_mappings'] = []
    flash('Cleared all exam session mappings.', 'info')
    return redirect(url_for('allocation_view'))

@app.route('/allocation/run', methods=['POST'])
@admin_required
def run_allocation_route():
    selected_mappings = session.get('session_mappings', [])
    result = run_seating_allocation(selected_mappings=selected_mappings)

    if result['status'] == 'success':
        msg = f"Allocation successful! Seated {result['allocated_count']} students across {result['halls_used']} halls. ({result.get('mode')})"
        flash(msg, 'success')
        # Send allocation emails to students
        email_res = send_allocation_emails()
        if email_res['status'] == 'success':
            flash(f"Emails sent to {email_res['sent']} students. ({email_res['mode']})", 'success')
        else:
            flash(email_res.get('message', 'Failed to send allocation emails.'), 'danger')
    else:
        flash(result['message'], 'danger')

    return redirect(url_for('allocation_view'))

@app.route('/allocation/clear', methods=['POST'])
@admin_required
def clear_allocation_route():
    models.clear_all_allocations()
    flash('All seating allocations have been cleared.', 'info')
    return redirect(url_for('allocation_view'))

@app.route('/allocation/send-emails', methods=['POST'])
@admin_required
def send_emails_route():
    res = send_allocation_emails()
    if res['status'] == 'success':
        flash(f"Emails sent successfully to {res['sent']} students from sakthipriyan1212@gmail.com! ({res['mode']})", 'success')
    else:
        flash(res['message'], 'danger')
    return redirect(url_for('allocation_view'))

@app.route('/allocation/save-settings', methods=['POST'])
@admin_required
def save_settings_route():
    settings = {
        'sender_email': request.form.get('sender_email', 'sakthipriyan1212@gmail.com').strip(),
        'smtp_server': request.form.get('smtp_server', 'smtp.gmail.com').strip(),
        'smtp_port': request.form.get('smtp_port', '587').strip(),
        'smtp_password': request.form.get('smtp_password', '').strip(),
        'simulation_mode': 'true' if request.form.get('simulation_mode') else 'false'
    }
    models.update_settings(settings)
    flash('Email sender settings updated.', 'success')
    return redirect(url_for('allocation_view'))

# --- Visual Seating View ---
@app.route('/seating-view')
@admin_required
def seating_view():
    hall_id = request.args.get('hall_id', type=int)
    halls = models.get_all_halls()

    if hall_id:
        display_halls = [h for h in halls if h['id'] == hall_id]
    else:
        display_halls = halls

    allocations = models.get_all_allocations()

    hall_bench_map = {}
    for a in allocations:
        key = (a['hall_id'], a['bench_row'], a['bench_col'])
        if key not in hall_bench_map:
            hall_bench_map[key] = []
        hall_bench_map[key].append(a)

    return render_template(
        'seating_view.html',
        halls=halls,
        display_halls=display_halls,
        selected_hall_id=hall_id,
        hall_bench_map=hall_bench_map
    )

# --- Student Search ---
@app.route('/search')
@admin_required
def search_view():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        results = models.get_all_allocations(search=query)
    return render_template('search.html', query=query, results=results)

# --- PDF Reports ---
@app.route('/reports')
@admin_required
def reports_view():
    return render_template('reports.html')

@app.route('/reports/pdf/<report_type>')
@admin_required
def export_pdf_route(report_type):
    hall_id = request.args.get('hall_id', type=int)

    if report_type == 'hall':
        pdf_buf = generate_hall_seating_pdf(hall_id)
        filename = 'Hall_Seating_Arrangement_Sheet.pdf'
    elif report_type == 'student':
        pdf_buf = generate_student_master_pdf()
        filename = 'Student_Master_Allocation_Sheet.pdf'
    elif report_type == 'invigilator':
        pdf_buf = generate_invigilator_pdf(hall_id)
        filename = 'Invigilator_Summary_Copy.pdf'
    elif report_type == 'attendance':
        pdf_buf = generate_attendance_sheet_pdf(hall_id)
        filename = 'Exam_Attendance_Sign_Sheet.pdf'
    else:
        flash('Invalid report type requested.', 'danger')
        return redirect(url_for('reports_view'))

    return send_file(pdf_buf, as_attachment=True, download_name=filename, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
