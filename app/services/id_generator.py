# backend/app/services/id_generator.py

from sqlalchemy import text
from app.database import db_dependency


def generate_school_id(role: str, enrollment_year: int, db: db_dependency) -> str:
    """
    Generate unique school ID: Kristobell/STU/YYYY/#### or Kristobell/STF/YYYY/####
    Uses PostgreSQL sequence for atomic increments (concurrency-safe)

    Args:
        role: 'student' or 'staff'
        enrollment_year: Year of enrollment (e.g., 2025)
        db: Database session

    Returns:
        Unique school ID string (e.g., "Kristobell/STU/2025/0001")
    """
    prefix = "Kristobell/STU" if role == "student" else "Kristobell/STF"
    year = str(enrollment_year)

    # Get or create sequence record and atomically increment
    result = db.execute(
        text(
            """
            INSERT INTO school_id_sequences (role, year, last_number)
            VALUES (:role, :year, 0)
            ON CONFLICT (role, year) DO UPDATE SET last_number = school_id_sequences.last_number + 1
            RETURNING last_number
        """
        ),
        {"role": role, "year": enrollment_year},
    )

    next_number = result.scalar()
    unique_id = f"{next_number:04d}"  # Format as 0001, 0002, etc.

    return f"{prefix}/{year}/{unique_id}"


# Preview endpoint (optional, for admin UI)
# GET /api/admin/id-preview?role=student&year=2025
