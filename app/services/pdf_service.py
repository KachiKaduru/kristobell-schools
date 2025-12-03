# backend/app/services/pdf_service.py

from weasyprint import HTML
from jinja2 import Template
import io
from datetime import datetime
from app.config import settings
from app.database import (
    get_student_with_profile,
    get_student_results,
    calculate_class_ranking,
)


async def generate_result_pdf(
    student_id: str, term: str, academic_year: str, db
) -> bytes:
    """
    Generate PDF result sheet for a student

    Returns:
        PDF bytes
    """
    # Fetch student data, results, class ranking
    student = get_student_with_profile(student_id, db)
    results = get_student_results(student_id, term, academic_year, db)
    ranking = calculate_class_ranking(student_id, term, academic_year, db)

    # Load template
    with open("app/templates/result_pdf.html", "r") as f:
        template = Template(f.read())

    # Render HTML
    html_content = template.render(
        school_logo_url=settings.SCHOOL_LOGO_URL,
        student_photo_url=student.profile.photo_url or "",
        student_name=student.full_name,
        school_id=student.school_id,
        class_name=student.profile.current_class.name,
        date_of_birth=student.profile.date_of_birth,
        gender=student.profile.gender,
        term=term.title(),
        academic_year=academic_year,
        results=results,
        total_average=ranking["average"],
        position=ranking["position"],
        remark=ranking["remark"],
        promoted_to=ranking.get("promoted_to"),
        current_date=datetime.now().strftime("%Y-%m-%d"),
    )

    # Generate PDF
    pdf_bytes = HTML(string=html_content).write_pdf()

    return pdf_bytes
