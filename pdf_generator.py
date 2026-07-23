import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from models import get_all_allocations, get_all_halls

def generate_hall_seating_pdf(hall_id=None):
    """
    Generates Hall-wise Seating Sheet PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e293b"),
        alignment=1, # Center
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=20
    )

    story.append(Paragraph("EXAM HALL SEATING ARRANGEMENT SHEET", title_style))
    story.append(Paragraph("Official Examination Hall Allocation Document", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

    allocations = get_all_allocations(hall_id=hall_id)
    halls = get_all_halls()

    if hall_id:
        halls = [h for h in halls if h['id'] == int(hall_id)]

    for hall in halls:
        h_allocs = [a for a in allocations if a['hall_id'] == hall['id']]
        if not h_allocs:
            continue

        hall_title = Paragraph(f"<b>{hall['hall_name']}</b> (Capacity: {hall['total_capacity']} | Allocated: {len(h_allocs)})", styles['Heading2'])
        story.append(hall_title)
        story.append(Spacer(1, 8))

        # Build Grid Table (Rows x Cols)
        rows = hall['rows']
        cols = hall['cols']

        # Map bench (r, c) -> list of seats
        bench_map = {}
        for a in h_allocs:
            key = (a['bench_row'], a['bench_col'])
            if key not in bench_map:
                bench_map[key] = []
            bench_map[key].append(a)

        # Table Header
        headers = ["Bench Row"] + [f"Column {c}" for c in range(1, cols + 1)]
        table_data = [headers]

        cell_style = ParagraphStyle('CellText', fontSize=8, leading=10, alignment=1)

        for r in range(1, rows + 1):
            row_cells = [f"Row {r}"]
            for c in range(1, cols + 1):
                seats = bench_map.get((r, c), [])
                if seats:
                    seat_texts = []
                    for s in seats:
                        code = s['dept_code'] or 'GEN'
                        seat_texts.append(f"<b>S{s['seat_position']}:</b> {s['reg_no']}<br/><font color='#2563eb'>({code})</font>")
                    cell_content = "<br/>----------------<br/>".join(seat_texts)
                else:
                    cell_content = "<font color='#94a3b8'>[ EMPTY ]</font>"

                row_cells.append(Paragraph(cell_content, cell_style))
            table_data.append(row_cells)

        grid_table = Table(table_data, colWidths=[65] + [(500/cols)]*cols)
        grid_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('BACKGROUND', (0,1), (0,-1), colors.HexColor("#f8fafc")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))

        story.append(grid_table)
        story.append(Spacer(1, 25))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_student_master_pdf():
    """
    Generates Student-wise Master Allocation Sheet PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("STUDENT SEATING ALLOCATION MASTER SHEET", ParagraphStyle('T', parent=styles['Heading1'], alignment=1)))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

    allocations = get_all_allocations()

    table_data = [["S.No", "Reg No", "Student Name", "Dept", "Subject", "Hall", "Bench (R/C)", "Seat"]]
    cell_style = ParagraphStyle('Cell', fontSize=9, leading=11)

    for idx, a in enumerate(allocations, 1):
        table_data.append([
            str(idx),
            a['reg_no'],
            Paragraph(a['student_name'], cell_style),
            a['dept_code'] or '',
            a['subject_code'] or 'N/A',
            a['hall_name'],
            f"R{a['bench_row']} - C{a['bench_col']}",
            f"Seat {a['seat_position']}"
        ])

    table = Table(table_data, colWidths=[30, 65, 120, 50, 70, 90, 70, 45])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))

    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_invigilator_pdf(hall_id=None):
    """
    Generates Invigilator Copy PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("EXAM HALL INVIGILATOR SUMMARY COPY", ParagraphStyle('T', parent=styles['Heading1'], alignment=1)))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

    allocations = get_all_allocations(hall_id=hall_id)
    halls = get_all_halls()

    if hall_id:
        halls = [h for h in halls if h['id'] == int(hall_id)]

    for hall in halls:
        h_allocs = [a for a in allocations if a['hall_id'] == hall['id']]
        if not h_allocs:
            continue

        story.append(Paragraph(f"<b>Hall:</b> {hall['hall_name']} | <b>Total Allocated:</b> {len(h_allocs)} / {hall['total_capacity']}", styles['Heading3']))
        story.append(Spacer(1, 5))

        table_data = [["Reg No", "Student Name", "Dept", "Subject", "Bench Pos", "Seat", "Invigilator Remarks"]]
        cell_style = ParagraphStyle('Cell', fontSize=9, leading=11)

        for a in h_allocs:
            table_data.append([
                a['reg_no'],
                Paragraph(a['student_name'], cell_style),
                a['dept_code'] or '',
                a['subject_code'] or '',
                f"R{a['bench_row']} C{a['bench_col']}",
                f"S{a['seat_position']}",
                ""
            ])

        table = Table(table_data, colWidths=[70, 130, 50, 70, 70, 45, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))

        story.append(table)
        story.append(Spacer(1, 20))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_attendance_sheet_pdf(hall_id=None):
    """
    Generates Student Attendance Sign Sheet PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("OFFICIAL EXAM ATTENDANCE SHEET", ParagraphStyle('T', parent=styles['Heading1'], alignment=1)))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))

    allocations = get_all_allocations(hall_id=hall_id)
    halls = get_all_halls()

    if hall_id:
        halls = [h for h in halls if h['id'] == int(hall_id)]

    for hall in halls:
        h_allocs = [a for a in allocations if a['hall_id'] == hall['id']]
        if not h_allocs:
            continue

        story.append(Paragraph(f"<b>Hall Name:</b> {hall['hall_name']} | <b>Date:</b> ______________ | <b>Session:</b> ________", styles['Heading3']))
        story.append(Spacer(1, 6))

        table_data = [["S.No", "Reg No", "Student Name", "Dept", "Bench", "Seat", "Status", "Student Signature"]]
        cell_style = ParagraphStyle('Cell', fontSize=9, leading=11)

        for idx, a in enumerate(h_allocs, 1):
            table_data.append([
                str(idx),
                a['reg_no'],
                Paragraph(a['student_name'], cell_style),
                a['dept_code'] or '',
                f"R{a['bench_row']}C{a['bench_col']}",
                f"Seat {a['seat_position']}",
                "Absent" if a['is_absent'] else "Present",
                ""
            ])

        table = Table(table_data, colWidths=[30, 70, 130, 50, 55, 45, 55, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))

        story.append(table)
        story.append(Spacer(1, 20))

    doc.build(story)
    buffer.seek(0)
    return buffer
