import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, select

from .celery_app import app
from .database import async_engine
from .models import Assignment, AssignmentLog, AssignmentStatus, User


async def get_async_db_session():
    """Get async database session for Celery tasks"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """Send email notification (stub implementation)"""
    # In production, configure actual SMTP settings
    smtp_server = os.getenv("SMTP_SERVER", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("FROM_EMAIL", "noreply@campusflow.example.com")

    try:
        # For development, just log the email
        print(f"📧 EMAIL NOTIFICATION (STUB)")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print(f"HTML Body: {html_body}")
        print("=" * 50)

        # Uncomment below for actual email sending in production
        # msg = MIMEMultipart('alternative')
        # msg['Subject'] = subject
        # msg['From'] = from_email
        # msg['To'] = to_email
        #
        # text_part = MIMEText(body, 'plain')
        # msg.attach(text_part)
        #
        # if html_body:
        #     html_part = MIMEText(html_body, 'html')
        #     msg.attach(html_part)
        #
        # server = smtplib.SMTP(smtp_server, smtp_port)
        # server.starttls()
        # server.login(smtp_username, smtp_password)
        # server.send_message(msg)
        # server.quit()

        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@app.task(bind=True)
def send_assignment_reminders(self):
    """Send reminders for assignments due tomorrow"""
    import asyncio

    async def _send_reminders():
        async for session in get_async_db_session():
            # Get assignments due tomorrow
            tomorrow = datetime.utcnow().date() + timedelta(days=1)
            tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
            tomorrow_end = datetime.combine(tomorrow, datetime.max.time())

            # Get assignments due tomorrow
            assignments_query = select(Assignment).where(
                and_(
                    Assignment.due_at >= tomorrow_start,
                    Assignment.due_at <= tomorrow_end,
                )
            )

            result = await session.exec(assignments_query)
            due_assignments = result.all()

            if not due_assignments:
                print("No assignments due tomorrow")
                return

            print(f"Found {len(due_assignments)} assignments due tomorrow")

            for assignment in due_assignments:
                # Get all students who haven't completed this assignment
                incomplete_logs_query = select(AssignmentLog).where(
                    and_(
                        AssignmentLog.assignment_id == assignment.id,
                        AssignmentLog.status != AssignmentStatus.COMPLETED,
                    )
                )

                result = await session.exec(incomplete_logs_query)
                incomplete_logs = result.all()

                # Get users who have logs but haven't completed
                user_ids_with_incomplete = [log.user_id for log in incomplete_logs]

                # Also get all students who don't have logs at all for this assignment
                users_with_logs_query = (
                    select(AssignmentLog.user_id)
                    .where(AssignmentLog.assignment_id == assignment.id)
                    .distinct()
                )

                users_with_logs_result = await session.exec(users_with_logs_query)
                users_with_logs = users_with_logs_result.all()

                # Get all students
                all_students_query = select(User).where(User.role == "student")
                all_students_result = await session.exec(all_students_query)
                all_students = all_students_result.all()

                # Find students without logs
                users_without_logs = [
                    user for user in all_students if user.id not in users_with_logs
                ]

                # Get users who need reminders
                users_needing_reminders = []

                # Add users with incomplete logs
                for log in incomplete_logs:
                    user_query = select(User).where(User.id == log.user_id)
                    user_result = await session.exec(user_query)
                    user = user_result.first()
                    if user:
                        users_needing_reminders.append(user)

                # Add users without logs
                users_needing_reminders.extend(users_without_logs)

                # Send reminders
                for user in users_needing_reminders:
                    subject = f"Assignment Reminder: {assignment.title} due tomorrow"
                    body = f"""
Hi {user.name},

This is a reminder that your assignment "{assignment.title}" for {assignment.subject} is due tomorrow ({assignment.due_at.strftime('%Y-%m-%d %H:%M')}).

{assignment.description or ''}

Please make sure to complete and submit your assignment on time.

Best regards,
CampusFlow Team
                    """.strip()

                    html_body = f"""
<html>
<body>
    <h2>Assignment Reminder</h2>
    <p>Hi {user.name},</p>
    <p>This is a reminder that your assignment <strong>"{assignment.title}"</strong> for {assignment.subject} is due tomorrow ({assignment.due_at.strftime('%Y-%m-%d %H:%M')}).</p>
    {f'<p>{assignment.description}</p>' if assignment.description else ''}
    <p>Please make sure to complete and submit your assignment on time.</p>
    <p>Best regards,<br>CampusFlow Team</p>
</body>
</html>
                    """.strip()

                    success = send_email(user.email, subject, body, html_body)
                    if success:
                        print(
                            f"Sent reminder to {user.email} for assignment {assignment.title}"
                        )
                    else:
                        print(
                            f"Failed to send reminder to {user.email} for assignment {assignment.title}"
                        )

    # Run the async function
    asyncio.run(_send_reminders())

    return "Assignment reminders sent successfully"


@app.task
def send_welcome_email(user_email: str, user_name: str):
    """Send welcome email to new user"""
    subject = "Welcome to CampusFlow!"
    body = f"""
Hi {user_name},

Welcome to CampusFlow! You've successfully logged in using your Google account.

CampusFlow helps you manage:
- Assignment deadlines and progress tracking
- School event calendar
- Important announcements

You can access the platform anytime at your convenience.

Best regards,
CampusFlow Team
    """.strip()

    html_body = f"""
<html>
<body>
    <h2>Welcome to CampusFlow!</h2>
    <p>Hi {user_name},</p>
    <p>Welcome to CampusFlow! You've successfully logged in using your Google account.</p>
    
    <h3>CampusFlow helps you manage:</h3>
    <ul>
        <li>Assignment deadlines and progress tracking</li>
        <li>School event calendar</li>
        <li>Important announcements</li>
    </ul>
    
    <p>You can access the platform anytime at your convenience.</p>
    
    <p>Best regards,<br>CampusFlow Team</p>
</body>
</html>
    """.strip()

    success = send_email(user_email, subject, body, html_body)
    return f"Welcome email sent to {user_email}: {success}"
