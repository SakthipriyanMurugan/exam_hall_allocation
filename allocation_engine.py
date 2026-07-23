import math
from models import get_all_halls, get_all_students, get_all_subjects, add_hall, save_allocations, get_db_connection

def generate_column_wise_bench_sequence(rows, cols):
    """
    Fills benches column-wise:
    R1C1, R2C1, R3C1, R4C1, R5C1,
    R1C2, R2C2, R3C2, R4C2, R5C2,
    R1C3, R2C3, R3C3, R4C3, R5C3
    """
    sequence = []
    for c in range(1, cols + 1):
        for r in range(1, rows + 1):
            sequence.append((r, c))
    return sequence

def reg_sort_key(s):
    """
    Sort key to preserve numerical register number order (e.g., 1001 < 1002 < 1010).
    """
    reg_str = str(s['reg_no']).strip()
    digits = ''.join(c for c in reg_str if c.isdigit())
    if digits:
        return (0, int(digits), reg_str)
    return (1, 0, reg_str)

def run_seating_allocation(selected_mappings=None):
    """
    Executes seating allocation algorithm following exact requirements:
    1. Student Sorting: Group by Dept/Subject, sort ascending by Register Number. Order NEVER changes.
    2. Column Allocation: Fill column-wise (R1C1..R5C1, R1C2..R5C2, R1C3..R5C3).
    3. Department Continuity: A department stays in its column stream (Left, Middle, Right) across benches & halls until exhausted.
    4. Single Remaining Department Rule:
       When only 1 department remains (or for extra leftover students of 1 dept), allocate as CIVIL | EMPTY | CIVIL on every bench!
    5. Overflow & Utilization: Continuous filling across halls without unnecessary empty seats.
    """
    all_students = get_all_students(is_absent=0)
    if not all_students:
        return {'status': 'error', 'message': 'No active students available for allocation.'}

    all_subjects = {s['id']: dict(s) for s in get_all_subjects()}

    student_objects = []

    if selected_mappings and len(selected_mappings) > 0:
        mapping_keys = {}
        for m in selected_mappings:
            key = (int(m['dept_id']), int(m['year']), int(m['semester']))
            mapping_keys[key] = int(m['subject_id']) if m.get('subject_id') else None

        for st in all_students:
            key = (st['dept_id'], st['year'], st['semester'])
            if key in mapping_keys:
                s_obj = dict(st)
                s_obj['subject_id'] = mapping_keys[key]
                sub_info = all_subjects.get(mapping_keys[key])
                if sub_info:
                    s_obj['subject_code'] = sub_info['subject_code']
                    s_obj['subject_name'] = sub_info['subject_name']
                student_objects.append(s_obj)
    else:
        subj_map = {}
        for s in all_subjects.values():
            key = (s['dept_id'], s['year'], s['semester'])
            subj_map[key] = s['id']

        for st in all_students:
            s_obj = dict(st)
            key = (st['dept_id'], st['year'], st['semester'])
            s_obj['subject_id'] = subj_map.get(key)
            sub_info = all_subjects.get(s_obj['subject_id'])
            if sub_info:
                s_obj['subject_code'] = sub_info['subject_code']
                s_obj['subject_name'] = sub_info['subject_name']
            student_objects.append(s_obj)

    if not student_objects:
        return {'status': 'error', 'message': 'No students match the selected exam department/year/semester mappings.'}

    # Group students by Department & Subject, then sort strictly by ascending Register Number
    dept_groups = {}
    for st in student_objects:
        d_id = st['dept_id'] or 0
        if d_id not in dept_groups:
            dept_groups[d_id] = []
        dept_groups[d_id].append(st)

    # Sort each department queue by ascending Register Number
    dept_queues = []
    for d_id in sorted(dept_groups.keys()):
        sorted_q = sorted(dept_groups[d_id], key=reg_sort_key)
        dept_queues.append({
            'dept_id': d_id,
            'dept_code': sorted_q[0].get('dept_code', 'GEN'),
            'students': sorted_q
        })

    # Prepare available halls & calculate capacity
    halls = [dict(h) for h in get_all_halls()]
    total_student_count = len(student_objects)

    total_hall_capacity = sum(h['total_capacity'] for h in halls)
    if total_hall_capacity < total_student_count:
        deficit = total_student_count - total_hall_capacity
        halls_to_add = math.ceil(deficit / 45)
        for i in range(1, halls_to_add + 1):
            hall_name = f"Auto-Generated Hall {len(halls) + i}"
            add_hall(hall_name, rows=5, cols=3, capacity_per_bench=3)
        halls = [dict(h) for h in get_all_halls()]

    # Global Bench Sequence across all halls (filled column-wise)
    bench_slots = []
    for hall in halls:
        rows = hall['rows']
        cols = hall['cols']
        seq = generate_column_wise_bench_sequence(rows, cols)
        for (r, c) in seq:
            bench_slots.append({
                'hall_id': hall['id'],
                'hall_name': hall['hall_name'],
                'row': r,
                'col': c,
                'capacity': hall['capacity_per_bench']
            })

    # SETUP 3 COLUMN STREAMS FOR BENCH SEATING:
    # Stream 0: Left Seat (Seat 1)
    # Stream 1: Middle Seat (Seat 2) - Separator
    # Stream 2: Right Seat (Seat 3)

    num_depts = len(dept_queues)

    if num_depts == 1:
        # SINGLE DEPARTMENT SPECIAL HANDLING:
        # Allocate as: CIVIL | [ EMPTY ] | CIVIL on every bench!
        q = dept_queues[0]['students']
        active_streams = {
            0: q,
            1: None, # Middle Seat MUST BE EMPTY!
            2: q
        }
    elif num_depts == 2:
        # 2 DEPARTMENTS: Seat 1 = Dept 1, Seat 2 = EMPTY, Seat 3 = Dept 2
        active_streams = {
            0: dept_queues[0]['students'],
            1: None, # Middle Seat EMPTY to separate Dept 1 and Dept 2!
            2: dept_queues[1]['students']
        }
    else:
        # 3 OR MORE DEPARTMENTS: Seat 1 = Dept 1, Seat 2 = Dept 2, Seat 3 = Dept 3
        active_streams = {
            0: dept_queues[0]['students'],
            1: dept_queues[1]['students'],
            2: dept_queues[2]['students']
        }
    
    # Initialize streams with first three departments
    active_streams = {
        0: dept_queues[0]['students'] if num_depts > 0 else None,
        1: dept_queues[1]['students'] if num_depts > 1 else None,
        2: dept_queues[2]['students'] if num_depts > 2 else None
    }

    next_dept_ptr = 3

    allocations = []

    for slot in bench_slots:
        # Determine remaining department queues (including those attached to streams)
        remaining_queues = [q for q in dept_queues if len(q['students']) > 0]
        if not remaining_queues:
            break

        # Assign streams based on number of remaining departments
        if len(remaining_queues) == 1:
            # Single department left → left & right same, middle empty
            active_streams = {
                0: remaining_queues[0]['students'],
                1: None,
                2: remaining_queues[0]['students']
            }
        elif len(remaining_queues) == 2:
            # Two departments left → left = first, right = second, middle empty
            active_streams = {
                0: remaining_queues[0]['students'],
                1: None,
                2: remaining_queues[1]['students']
            }
        else:
            # Three or more departments – preserve existing streams, replace any empty stream
            for stream_key in (0, 1, 2):
                if not active_streams.get(stream_key) or len(active_streams[stream_key]) == 0:
                    # Find a queue not already used in other streams
                    used_ids = {id(active_streams.get(k)) for k in (0, 1, 2) if active_streams.get(k)}
                    for q in remaining_queues:
                        if id(q['students']) not in used_ids:
                            active_streams[stream_key] = q['students']
                            used_ids.add(id(q['students']))
                            break
            # Ensure all three keys exist (may be None)
            active_streams.setdefault(0, None)
            active_streams.setdefault(1, None)
            active_streams.setdefault(2, None)

        hall_id = slot['hall_id']
        r = slot['row']
        c = slot['col']
        cap = slot['capacity']

        seats_to_fill = [1, 2, 3] if cap == 3 else [1, 3]

        for seat_pos in seats_to_fill:
            stream_key = seat_pos - 1  # 0 for Seat 1, 1 for Seat 2, 2 for Seat 3
            q_stream = active_streams.get(stream_key)
            if q_stream:
                student = q_stream.pop(0)
                allocations.append({
                    'student_id': student['id'],
                    'hall_id': hall_id,
                    'bench_row': r,
                    'bench_col': c,
                    'seat_position': seat_pos,
                    'subject_id': student.get('subject_id'),
                    'student_name': student['name'],
                    'reg_no': student['reg_no'],
                    'email': student.get('email'),
                    'dept_id': student['dept_id'],
                    'subject_code': student.get('subject_code')
                })

    save_allocations(allocations)

    return {
        'status': 'success',
        'allocated_count': len(allocations),
        'halls_used': len(set(a['hall_id'] for a in allocations)),
        'mode': f"Column-Wise Continuity Stream Mode ({num_depts} Depts)",
        'conflicts_count': 0,
        'conflicts': []
    }
