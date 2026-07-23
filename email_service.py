import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import get_all_allocations, get_settings

def send_allocation_emails():
    """
    Sends customized hall allocation email notifications to all allocated students
    from sakthipriyan1212@gmail.com.
    Supports both real SMTP dispatch and local simulation logging.
    """
    settings = get_settings()
    sender_email = settings.get('sender_email', 'sakthipriyan1212@gmail.com')
    smtp_server = settings.get('smtp_server', 'smtp.gmail.com')
    smtp_port = int(settings.get('smtp_port', 587))
    smtp_password = settings.get('smtp_password', '').strip()
    simulation_mode = settings.get('simulation_mode', 'true').lower() == 'true'

    allocations = get_all_allocations()
    if not allocations:
        return {'status': 'error', 'message': 'No allocations found to send emails.'}

    success_count = 0
    failed_count = 0
    logs = []

    server = None
    if not simulation_mode and smtp_password:
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, smtp_password)
        except Exception as e:
            simulation_mode = True
            logs.append(f"SMTP connection error: {str(e)}. Falling back to simulation mode.")

    for alloc in allocations:
        recipient_email = alloc['email']
        student_name = alloc['student_name']
        reg_no = alloc['reg_no']
        hall_name = alloc['hall_name']
        bench_row = alloc['bench_row']
        bench_col = alloc['bench_col']
        seat_pos = alloc['seat_position']
        subject_name = alloc['subject_name'] or alloc['subject_code'] or 'General Examination'

        subject = f"Exam Hall Allocation Details - {reg_no} - {hall_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0;">
                <h2 style="color: #1e293b; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">Exam Hall Allocation Slip</h2>
                <p>Dear <strong>{student_name}</strong> ({reg_no}),</p>
                <p>Your seating allocation details for your upcoming examination are provided below:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background: #f1f5f9;">
                        <td style="padding: 10px; border: 1px solid #cbd5e1;"><strong>Register Number</strong></td>
                        <td style="padding: 10px; border: 1px solid #cbd5e1;">{reg_no}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #cbd5e1;"><strong>Subject</strong></td>
                        <td style="padding: 10px; border: 1px solid #cbd5e1;">{subject_name}</td>
                    </tr>
                    <tr style="background: #f1f5f9;">
                        <td style="padding: 10px; border: 1px solid #cbd5e1;"><strong>Allocated Hall</strong></td>
                        <td style="padding: 10px; border: 1px solid #cbd5e1; color: #2563eb; font-weight: bold;">{hall_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #cbd5e1;"><strong>Bench Position</strong></td>
                        <td style="padding: 10px; border: 1px solid #cbd5e1;">Row {bench_row}, Column {bench_col}</td>
                    </tr>
                    <tr style="background: #f1f5f9;">
                        <td style="padding: 10px; border: 1px solid #cbd5e1;"><strong>Seat Number</strong></td>
                        <td style="padding: 10px; border: 1px solid #cbd5e1; font-weight: bold;">Seat {seat_pos}</td>
                    </tr>
                </table>
                
                <p style="color: #64748b; font-size: 13px;">Please arrive at the examination hall at least 15 minutes before the scheduled exam start time with your official ID card.</p>
                <hr style="border: 0; border-top: 1px solid #e2e8f0; margin-top: 20px;">
                <p style="font-size: 12px; color: #94a3b8; text-align: center;">Sent by Examination Office via {sender_email}</p>
            </div>
        </body>
        </html>
        """

        if simulation_mode or not server:
            # Simulate email dispatch
            success_count += 1
            logs.append(f"[SIMULATION EMAIL SENT] From: {sender_email} -> To: {recipient_email} | Student: {name_safe(student_name)} | Hall: {hall_name} (Row {bench_row} Col {bench_col} Seat {seat_pos})")
        else:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"Exam Controller <{sender_email}>"
                msg['To'] = recipient_email
                msg.attach(MIMEText(html_body, 'html'))

                server.sendmail(sender_email, recipient_email, msg.as_string())
                success_count += 1
                logs.append(f"[LIVE EMAIL SENT] From: {sender_email} -> To: {recipient_email}")
            except Exception as e:
                failed_count += 1
                logs.append(f"[EMAIL FAILED] To: {recipient_email} - Error: {str(e)}")

    if server:
        try:
            server.quit()
        except:
            pass

    return {
        'status': 'success',
        'total': len(allocations),
        'sent': success_count,
        'failed': failed_count,
        'mode': 'Simulated Log Mode' if simulation_mode else 'Live SMTP Mode',
        'logs': logs[:50] # return top logs
    }

def name_safe(name):
    return name.encode('ascii', 'ignore').decode('ascii')
