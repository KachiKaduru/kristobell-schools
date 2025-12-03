# Kristobell School Management System - Technical Implementation Plan

## MVP Scope & Summary

**Goal (MVP):** Deliver a functional Admin + Staff + Student portal that supports the real class structure (47 classes), secure authentication, ID generation, CRUD for classes/students/staff, assignment/result upload, student read-only profiles with passport images, and Result PDF export.

**Why MVP First:** With ~515-720 students across 47 classes, scope can expand quickly. Focus on core school operations first, then add advanced features (attendance, payments, etc.) in later phases.

---

## School Structure (Exact Specification)

### Class Structure & Capacity

**Early Years:**

- **KG 1A, KG 1B** → **KG 2A, KG 2B** (4 classes, 15 pupils/class = 60 max)

**Nursery:**

- **NUR 1A, NUR 1B** → **NUR 2A, NUR 2B** (4 classes, 20 pupils/class = 80 max)

**Primary:**

- **PRY 1A, PRY 1B, PRY 1C** → **PRY 5A, PRY 5B, PRY 5C** (15 classes, 25 pupils/class = 375 max)

**Junior Secondary:**

- **JSS 1A, JSS 1B, JSS 1C, JSS 1D** → **JSS 3A, JSS 3B, JSS 3C, JSS 3D** (12 classes, 30 students/class = 360 max)

**Senior Secondary:**

- **SSS 1A, SSS 1B, SSS 1C, SSS 1D** → **SSS 3A, SSS 3B, SSS 3C, SSS 3D** (12 classes, 30 students/class = 360 max)
- **SSS Stream Mapping by Arm:**
  - **SSS A** = Science
  - **SSS B** = Technical
  - **SSS C** = Commercial
  - **SSS D** = Arts

**Totals:**

- **47 classes total** (23 in Nursery/Primary, 24 in Secondary)
- **~515-720 students** depending on fill rates
- Design assumes high-side capacity for performance

---

## System Architecture

```
┌─────────────────────────────────────────┐
│         Next.js Frontend (SSR)         │
│  ┌───────────────────────────────────┐  │
│  │  Landing Page (Public)            │  │
│  │  - Enrollment Form                │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Portal Routes (Protected)        │  │
│  │  - Admin / Staff / Student        │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌───────────────────────────────────┐  │
│  │  Authentication Service            │  │
│  │  - JWT Token Generation           │  │
│  │  - Role-based Auth                │  │
│  │  - Refresh Tokens                 │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Business Logic Services          │  │
│  │  - ID Generation (DB sequences)   │  │
│  │  - Result Calculation             │  │
│  │  - Enrollment Processing          │  │
│  │  - PDF Generation                 │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  File Upload Service               │  │
│  │  - Presigned URLs                  │  │
│  │  - Photo Management                │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  API Routes (REST)                │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │  File Storage│
│   Database   │  │  (Supabase)  │
└──────────────┘  └──────────────┘
```

---

## Database Schema Design (SQLAlchemy Models)

### Design Principles

- **Single auth source** (`users` table) to avoid duplication
- **Profile tables** (`student_profiles`, `staff_profiles`) for extended info
- **UUID primary keys** + **Postgres sequences** for school IDs (concurrency-safe)
- **Indexes** on `school_id`, `current_class_id`, `class_id`, `subject_id`, `academic_year`, `term`
- **Soft deletes** (`is_deleted`) for data retention
- **Capacity tracking** (`capacity`, `current_count`) on classes

### Database Setup (SQLite for Development)

```python
# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# For development: SQLite
# For production: PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./kristobell_school.db"  # Default to SQLite
)

# SQLite needs special handling for foreign keys
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite only
        echo=True  # Set to False in production
    )
else:
    engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Core Models

#### 1. **User Model** (Base authentication table)

```python
# backend/app/models/user.py

from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)  # Only for Admin
    school_id = Column(String(50), unique=True, nullable=True)  # For Staff/Students
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin', 'staff', 'student'
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    admin_profile = relationship("Admin", back_populates="user", uselist=False)
    staff_profile = relationship("StaffProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)

    # Indexes
    __table_args__ = (
        Index('idx_users_school_id', 'school_id'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, role={self.role}, school_id={self.school_id})>"
```

#### 2. **Admin Model** (Admin profile)

```python
# backend/app/models/admin.py

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="admin_profile")

    def __repr__(self):
        return f"<Admin(id={self.id})>"
```

#### 3. **StaffProfile Model** (Staff extended information)

```python
# backend/app/models/staff.py

from sqlalchemy import Column, String, Date, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    employment_date = Column(Date, nullable=False)
    is_form_teacher = Column(Boolean, default=False)
    photo_url = Column(String, nullable=True)  # URL to stored passport photo
    photo_etag = Column(String(255), nullable=True)  # For cache busting
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="staff_profile")

    def __repr__(self):
        return f"<StaffProfile(user_id={self.user_id})>"
```

#### 4. **StudentProfile Model** (Student extended information)

```python
# backend/app/models/student.py

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)  # 'male', 'female', 'other'
    parent_name = Column(String(255), nullable=False)
    parent_phone = Column(String(20), nullable=False)
    parent_email = Column(String(255), nullable=True)
    enrollment_year = Column(Integer, nullable=False)  # Extracted from school_id
    enrollment_status = Column(
        String(20),
        default='pending',
        nullable=False
    )  # 'pending', 'approved', 'rejected'
    current_class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True
    )
    photo_url = Column(String, nullable=True)  # URL to stored passport photo
    photo_etag = Column(String(255), nullable=True)  # For cache busting
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="student_profile")
    current_class = relationship("Class", foreign_keys=[current_class_id])

    # Constraints
    __table_args__ = (
        CheckConstraint("gender IN ('male', 'female', 'other')", name="check_gender"),
        CheckConstraint(
            "enrollment_status IN ('pending', 'approved', 'rejected')",
            name="check_enrollment_status"
        ),
        Index('idx_student_profiles_class', 'current_class_id'),
        Index('idx_student_profiles_enrollment_year', 'enrollment_year'),
    )

    def __repr__(self):
        return f"<StudentProfile(user_id={self.user_id})>"
```

#### 5. **Class Model** (Class management with capacity tracking)

```python
# backend/app/models/class.py

from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name = Column(String(50), nullable=False)  # e.g., "KG 1A", "JSS 2B", "SSS 3C"
    level = Column(String(20), nullable=False)  # 'kg', 'nursery', 'primary', 'jss', 'sss'
    arm_letter = Column(String(1), nullable=True)  # 'A', 'B', 'C', 'D'
    stream = Column(String(20), nullable=True)  # 'science', 'technical', 'commercial', 'arts' (only for SSS)
    academic_year = Column(String(20), nullable=False)  # e.g., "2024/2025"
    capacity = Column(Integer, nullable=False)  # Max students (15, 20, 25, or 30)
    current_count = Column(Integer, default=0)  # Current enrolled students
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    students = relationship("StudentProfile", foreign_keys="StudentProfile.current_class_id", back_populates="current_class")
    class_subjects = relationship("ClassSubject", back_populates="class_obj", cascade="all, delete-orphan")
    form_teachers = relationship("ClassFormTeacher", back_populates="class_obj", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'academic_year', name='uq_class_name_year'),
        CheckConstraint(
            "level IN ('kg', 'nursery', 'primary', 'jss', 'sss')",
            name="check_level"
        ),
        CheckConstraint(
            "stream IN ('science', 'technical', 'commercial', 'arts') OR stream IS NULL",
            name="check_stream"
        ),
        Index('idx_classes_level', 'level'),
        Index('idx_classes_academic_year', 'academic_year'),
        Index('idx_classes_stream', 'stream'),
    )

    def __repr__(self):
        return f"<Class(id={self.id}, name={self.name}, level={self.level})>"
```

**Class Naming Convention:**

- Format: `{LEVEL} {YEAR}{ARM}` (e.g., "KG 1A", "PRY 3B", "JSS 2C", "SSS 1A")
- Stream is derived from arm for SSS: A=Science, B=Technical, C=Commercial, D=Arts

#### 6. **Subject Model** (Subject catalog)

```python
# backend/app/models/subject.py

from sqlalchemy import Column, String, DateTime, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # e.g., "MTH101", "NUM001"
    level = Column(String(20), nullable=False)  # 'kg', 'nursery', 'primary', 'jss', 'sss'
    stream = Column(String(20), nullable=True)  # 'science', 'technical', 'commercial', 'arts' (only for SSS)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    class_subjects = relationship("ClassSubject", back_populates="subject", cascade="all, delete-orphan")
    staff_assignments = relationship("StaffSubjectAssignment", back_populates="subject", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "level IN ('kg', 'nursery', 'primary', 'jss', 'sss')",
            name="check_subject_level"
        ),
        CheckConstraint(
            "stream IN ('science', 'technical', 'commercial', 'arts') OR stream IS NULL",
            name="check_subject_stream"
        ),
        Index('idx_subjects_level', 'level'),
        Index('idx_subjects_stream', 'stream'),
    )

    def __repr__(self):
        return f"<Subject(id={self.id}, name={self.name}, code={self.code})>"
```

#### 7. **ClassSubject Model** (Many-to-Many: Classes ↔ Subjects)

```python
# backend/app/models/class_subject.py

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class ClassSubject(Base):
    __tablename__ = "class_subjects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False
    )
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    class_obj = relationship("Class", back_populates="class_subjects")
    subject = relationship("Subject", back_populates="class_subjects")

    # Constraints
    __table_args__ = (
        UniqueConstraint('class_id', 'subject_id', name='uq_class_subject'),
        Index('idx_class_subjects_class', 'class_id'),
        Index('idx_class_subjects_subject', 'subject_id'),
    )

    def __repr__(self):
        return f"<ClassSubject(class_id={self.class_id}, subject_id={self.subject_id})>"
```

#### 8. **StaffSubjectAssignment Model** (Many-to-Many: Staff ↔ Subjects ↔ Classes)

```python
# backend/app/models/staff_subject_assignment.py

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class StaffSubjectAssignment(Base):
    __tablename__ = "staff_subject_assignments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    staff_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False
    )
    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False
    )
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )  # Admin who assigned

    # Relationships
    staff = relationship("User", foreign_keys=[staff_id])
    subject = relationship("Subject", back_populates="staff_assignments")
    class_obj = relationship("Class")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint('staff_id', 'subject_id', 'class_id', name='uq_staff_subject_class'),
        Index('idx_staff_assignments_staff', 'staff_id'),
        Index('idx_staff_assignments_class', 'class_id'),
    )

    def __repr__(self):
        return f"<StaffSubjectAssignment(staff_id={self.staff_id}, subject_id={self.subject_id}, class_id={self.class_id})>"
```

#### 9. **ClassFormTeacher Model** (Form teacher assignments)

```python
# backend/app/models/class_form_teacher.py

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class ClassFormTeacher(Base):
    __tablename__ = "class_form_teachers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False
    )
    staff_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )  # Admin

    # Relationships
    class_obj = relationship("Class", back_populates="form_teachers")
    staff = relationship("User", foreign_keys=[staff_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint('class_id', 'staff_id', name='uq_class_form_teacher'),
        Index('idx_form_teachers_class', 'class_id'),
        Index('idx_form_teachers_staff', 'staff_id'),
    )

    def __repr__(self):
        return f"<ClassFormTeacher(class_id={self.class_id}, staff_id={self.staff_id})>"
```

#### 10. **EnrollmentRequest Model** (Public enrollment submissions)

```python
# backend/app/models/enrollment_request.py

from sqlalchemy import Column, String, Date, Text, DateTime, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class EnrollmentRequest(Base):
    __tablename__ = "enrollment_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)  # 'male', 'female', 'other'
    parent_name = Column(String(255), nullable=False)
    parent_phone = Column(String(20), nullable=False)
    parent_email = Column(String(255), nullable=True)
    requested_class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False
    )
    status = Column(
        String(20),
        default='pending',
        nullable=False
    )  # 'pending', 'approved', 'rejected'
    token = Column(String(255), unique=True, nullable=True)  # For public status lookup
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )  # Admin

    # Relationships
    requested_class = relationship("Class")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Constraints
    __table_args__ = (
        CheckConstraint("gender IN ('male', 'female', 'other')", name="check_enrollment_gender"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="check_enrollment_status"
        ),
        Index('idx_enrollment_status', 'status'),
        Index('idx_enrollment_token', 'token'),
    )

    def __repr__(self):
        return f"<EnrollmentRequest(id={self.id}, full_name={self.full_name}, status={self.status})>"
```

#### 11. **Assignment Model** (Staff-created assignments)

```python
# backend/app/models/assignment.py

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False
    )
    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )  # Staff member
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subject = relationship("Subject")
    class_obj = relationship("Class")
    creator = relationship("User", foreign_keys=[created_by])
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_assignments_class', 'class_id'),
        Index('idx_assignments_created_by', 'created_by'),
    )

    def __repr__(self):
        return f"<Assignment(id={self.id}, title={self.title})>"
```

#### 12. **AssignmentSubmission Model** (Student submissions)

```python
# backend/app/models/assignment_submission.py

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    response = Column(Text, nullable=True)
    file_url = Column(String, nullable=True)  # Optional file attachment URL
    status = Column(
        String(20),
        default='submitted',
        nullable=False
    )  # 'submitted', 'seen'
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    seen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint('assignment_id', 'student_id', name='uq_assignment_student'),
        CheckConstraint("status IN ('submitted', 'seen')", name="check_submission_status"),
        Index('idx_submissions_assignment', 'assignment_id'),
        Index('idx_submissions_student', 'student_id'),
    )

    def __repr__(self):
        return f"<AssignmentSubmission(id={self.id}, assignment_id={self.assignment_id}, student_id={self.student_id})>"
```

#### 13. **Result Model** (Student results by term)

```python
# backend/app/models/result.py

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Result(Base):
    __tablename__ = "results"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False
    )
    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False
    )
    academic_year = Column(String(20), nullable=False)  # e.g., "2024/2025"
    term = Column(String(20), nullable=False)  # 'first', 'second', 'third'
    level = Column(String(20), nullable=False)  # 'kg', 'nursery', 'primary', 'jss', 'sss'

    # For KG, Nursery, Primary: 1 CA (40 max) + Exam (60 max)
    ca_score = Column(Numeric(5, 2), nullable=True)  # Only for kg/nursery/primary
    exam_score = Column(Numeric(5, 2), nullable=False)

    # For JSS, SSS: 2 CAs (20 each) + Exam (60)
    first_ca = Column(Numeric(5, 2), nullable=True)  # Only for jss/sss
    second_ca = Column(Numeric(5, 2), nullable=True)  # Only for jss/sss

    total_score = Column(Numeric(5, 2), nullable=False)  # Calculated
    grade = Column(String(2), nullable=False)  # A, B, C, D, F

    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )  # Staff member
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    subject = relationship("Subject")
    class_obj = relationship("Class")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'academic_year', 'term', name='uq_result_student_subject_term'),
        CheckConstraint("term IN ('first', 'second', 'third')", name="check_term"),
        CheckConstraint(
            "level IN ('kg', 'nursery', 'primary', 'jss', 'sss')",
            name="check_result_level"
        ),
        Index('idx_results_student', 'student_id'),
        Index('idx_results_class', 'class_id'),
        Index('idx_results_academic_year', 'academic_year'),
        Index('idx_results_term', 'term'),
        Index('idx_results_subject', 'subject_id'),
    )

    def __repr__(self):
        return f"<Result(id={self.id}, student_id={self.student_id}, subject_id={self.subject_id}, term={self.term})>"
```

#### 14. **Announcement Model** (School announcements)

```python
# backend/app/models/announcement.py

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    header = Column(String(255), nullable=False)
    about = Column(String(500), nullable=True)  # Short description
    message = Column(Text, nullable=False)
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )  # Admin
    audience = Column(String(20), nullable=False)  # 'staff', 'students', 'both'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    author = relationship("User", foreign_keys=[author_id])

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "audience IN ('staff', 'students', 'both')",
            name="check_announcement_audience"
        ),
        Index('idx_announcements_audience', 'audience'),
        Index('idx_announcements_created', 'created_at'),
    )

    def __repr__(self):
        return f"<Announcement(id={self.id}, header={self.header}, audience={self.audience})>"
```

#### 15. **StudentPromotion Model** (Audit trail for promotions)

```python
# backend/app/models/student_promotion.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class StudentPromotion(Base):
    __tablename__ = "student_promotions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    from_class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False
    )
    to_class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False
    )
    academic_year = Column(String(20), nullable=False)
    promoted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )  # Admin
    promoted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    from_class = relationship("Class", foreign_keys=[from_class_id])
    to_class = relationship("Class", foreign_keys=[to_class_id])
    promoter = relationship("User", foreign_keys=[promoted_by])

    # Indexes
    __table_args__ = (
        Index('idx_promotions_student', 'student_id'),
    )

    def __repr__(self):
        return f"<StudentPromotion(id={self.id}, student_id={self.student_id}, from_class={self.from_class_id}, to_class={self.to_class_id})>"
```

#### 16. **SchoolIdSequence Model** (For atomic ID generation)

```python
# backend/app/models/school_id_sequence.py

from sqlalchemy import Column, String, Integer, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base

class SchoolIdSequence(Base):
    __tablename__ = "school_id_sequences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(20), nullable=False)  # 'student', 'staff'
    year = Column(Integer, nullable=False)
    last_number = Column(Integer, default=0)

    # Constraints
    __table_args__ = (
        UniqueConstraint('role', 'year', name='uq_role_year'),
        CheckConstraint("role IN ('student', 'staff')", name="check_sequence_role"),
        Index('idx_sequences_role_year', 'role', 'year'),
    )

    def __repr__(self):
        return f"<SchoolIdSequence(role={self.role}, year={self.year}, last_number={self.last_number})>"
```

### Models Initialization

```python
# backend/app/models/__init__.py

from app.models.user import User
from app.models.admin import Admin
from app.models.staff import StaffProfile
from app.models.student import StudentProfile
from app.models.class import Class
from app.models.subject import Subject
from app.models.class_subject import ClassSubject
from app.models.staff_subject_assignment import StaffSubjectAssignment
from app.models.class_form_teacher import ClassFormTeacher
from app.models.enrollment_request import EnrollmentRequest
from app.models.assignment import Assignment
from app.models.assignment_submission import AssignmentSubmission
from app.models.result import Result
from app.models.announcement import Announcement
from app.models.student_promotion import StudentPromotion
from app.models.school_id_sequence import SchoolIdSequence

__all__ = [
    "User",
    "Admin",
    "StaffProfile",
    "StudentProfile",
    "Class",
    "Subject",
    "ClassSubject",
    "StaffSubjectAssignment",
    "ClassFormTeacher",
    "EnrollmentRequest",
    "Assignment",
    "AssignmentSubmission",
    "Result",
    "Announcement",
    "StudentPromotion",
    "SchoolIdSequence",
]
```

### Database Initialization Script

```python
# backend/app/init_db.py

from app.database import Base, engine
from app.models import *  # Import all models

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
```

### Notes for SQLite vs PostgreSQL

**SQLite (Development):**

- Uses `INTEGER` for auto-incrementing IDs (works fine)
- UUIDs stored as strings (SQLAlchemy handles this)
- No native UUID type, but SQLAlchemy's UUID works
- Foreign keys need to be enabled: `PRAGMA foreign_keys = ON;` (add to database.py)

**PostgreSQL (Production):**

- Native UUID support
- Better performance for large datasets
- More advanced features (full-text search, JSON fields, etc.)

**Migration Path:**

1. Develop with SQLite locally
2. Test thoroughly
3. When ready for production, switch to PostgreSQL
4. Use Alembic migrations to handle differences
5. Export SQLite data and import to PostgreSQL if needed

The models above are compatible with both databases!
