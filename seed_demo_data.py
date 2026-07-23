from database import get_db_connection, init_db
from models import get_or_create_department

def seed_data():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]

    if count == 0:
        print("Seeding sample student and subject records...")
        
        # Ensure Departments
        cse = get_or_create_department('CSE', 'Computer Science Engineering')
        ece = get_or_create_department('ECE', 'Electronics Communication Engg')
        eee = get_or_create_department('EEE', 'Electrical Electronics Engg')
        mech = get_or_create_department('MECH', 'Mechanical Engineering')
        civil = get_or_create_department('CIVIL', 'Civil Engineering')

        # Add Subjects
        subjects = [
            (cse, 'CS8591', 'Computer Networks', 3, 5),
            (ece, 'EC8501', 'Digital Communication', 3, 5),
            (eee, 'EE8502', 'Power Electronics', 3, 5),
            (mech, 'ME8592', 'Thermal Engineering', 3, 5),
            (civil, 'CE8503', 'Structural Analysis', 3, 5)
        ]
        for dept_id, code, name, yr, sem in subjects:
            cursor.execute(
                "INSERT OR IGNORE INTO subjects (dept_id, subject_code, subject_name, year, semester) VALUES (?, ?, ?, ?, ?)",
                (dept_id, code, name, yr, sem)
            )

        # Add 60 Sample Students across departments
        sample_students = []
        
        # CSE Students (1001 - 1015)
        for i in range(1, 16):
            reg = str(1000 + i)
            names = ["Arun", "Bala", "Charan", "Divya", "Elan", "Farooq", "Gokul", "Hari", "Indu", "Jaya", "Kavya", "Lokesh", "Mani", "Naveen", "Oviya"]
            name = names[i-1]
            sample_students.append((reg, name, cse, 3, 5, f"{name.lower()}@gmail.com"))

        # ECE Students (2001 - 2015)
        for i in range(1, 16):
            reg = str(2000 + i)
            names = ["Priya", "Qadir", "Rahul", "Surya", "Tamil", "Usha", "Vijay", "William", "Xavier", "Yash", "Zara", "Aravind", "Bharath", "Chandru", "Deepak"]
            name = names[i-1]
            sample_students.append((reg, name, ece, 3, 5, f"{name.lower()}@gmail.com"))

        # EEE Students (3001 - 3015)
        for i in range(1, 16):
            reg = str(3000 + i)
            names = ["Ezhil", "Ganesh", "Hema", "Ishwarya", "Janani", "Karthik", "Lakshmi", "Meena", "Nirmal", "Omkar", "Prabhu", "Ramya", "Sangeetha", "Thangam", "Uma"]
            name = names[i-1]
            sample_students.append((reg, name, eee, 3, 5, f"{name.lower()}@gmail.com"))

        # MECH Students (4001 - 4015)
        for i in range(1, 16):
            reg = str(4000 + i)
            names = ["Vasudevan", "Vikram", "Vimal", "Vishnu", "Yamini", "Yogesh", "Zahir", "Abinesh", "Anand", "Babu", "Dinesh", "Gautam", "Jagan", "Kannan", "Madhavan"]
            name = names[i-1]
            sample_students.append((reg, name, mech, 3, 5, f"{name.lower()}@gmail.com"))

        cursor.executemany(
            "INSERT OR IGNORE INTO students (reg_no, name, dept_id, year, semester, email) VALUES (?, ?, ?, ?, ?, ?)",
            sample_students
        )

        conn.commit()
        print(f"Seeded {len(sample_students)} students successfully!")

    conn.close()

if __name__ == '__main__':
    seed_data()
