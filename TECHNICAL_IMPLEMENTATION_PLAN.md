# Kristobell School Management System - Technical Implementation Plan

## MVP Scope & Summary

**Goal (MVP):** Deliver a functional Admin + Staff + Student portal that supports the real class structure (47 classes), secure authentication, ID generation, CRUD for classes/students/staff, assignment/result upload, student read-only profiles with passport images, and Result PDF export.

**Why MVP First:** With ~515-720 students across 47 classes, scope can expand quickly. Focus on core school operations first, then add advanced features (attendance, payments, etc.) in later phases.

---

## Tech Stack Recommendation

### Backend

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Production database (SQLite for development)
- **Pydantic** - Data validation (comes with FastAPI)
- **JWT** (python-jose) - Authentication tokens
- **Passlib** + **bcrypt** - Password hashing
- **Alembic** - Database migrations
- **WeasyPrint** or **Playwright** - PDF generation
- **Redis** (optional) - Caching & background jobs
- **Celery** or **RQ** (optional) - Background task queue

### Frontend

- **Next.js 14+ (App Router)** - Recommended for SSR and better DX
- **TypeScript** - Type safety
- **React Query (TanStack Query)** - Server state management
- **Zustand** - Client-side state management
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Hook Form** - Form handling

### File Storage

- **Supabase Storage** (recommended for MVP) or **AWS S3** / **DigitalOcean Spaces**
- Direct client uploads via presigned URLs

### Additional Tools

- **Docker** (optional) - Containerization
- **Git** - Version control
- **Sentry** (optional) - Error monitoring

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

## Database Schema Design (Consolidated & Production-Ready)

### Design Principles

- **Single auth source** (`users` table) to avoid duplication
- **Profile tables** (`student_profiles`, `staff_profiles`) for extended info
- **UUID primary keys** + **Postgres sequences** for school IDs (concurrency-safe)
- **Indexes** on `school_id`, `current_class_id`, `class_id`, `subject_id`, `academic_year`, `term`
- **Soft deletes** (`is_deleted`) for data retention
- **Capacity tracking** (`capacity`, `current_count`) on classes

### Core Tables

#### 1. **users** (Base authentication table)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE, -- Nullable, only for Admin
    school_id VARCHAR(50) UNIQUE, -- Nullable, for Staff/Students (Kristobell/STU|STF/YYYY/####)
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'staff', 'student')),
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_school_id ON users(school_id) WHERE school_id IS NOT NULL;
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_role ON users(role);
```

#### 2. **admins** (Admin profile - minimal, most info in users)

```sql
CREATE TABLE admins (
    id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. **staff_profiles** (Staff extended information)

```sql
CREATE TABLE staff_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    date_of_birth DATE,
    employment_date DATE NOT NULL,
    is_form_teacher BOOLEAN DEFAULT FALSE,
    photo_url TEXT, -- URL to stored passport photo
    photo_etag VARCHAR(255), -- For cache busting
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. **student_profiles** (Student extended information)

```sql
CREATE TABLE student_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    parent_name VARCHAR(255) NOT NULL,
    parent_phone VARCHAR(20) NOT NULL,
    parent_email VARCHAR(255),
    enrollment_year INTEGER NOT NULL, -- Extracted from school_id
    enrollment_status VARCHAR(20) DEFAULT 'pending' CHECK (enrollment_status IN ('pending', 'approved', 'rejected')),
    current_class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    photo_url TEXT, -- URL to stored passport photo
    photo_etag VARCHAR(255), -- For cache busting
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_student_profiles_class ON student_profiles(current_class_id);
CREATE INDEX idx_student_profiles_enrollment_year ON student_profiles(enrollment_year);
```

#### 5. **classes** (Class management with capacity tracking)

```sql
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL, -- e.g., "KG 1A", "JSS 2B", "SSS 3C"
    level VARCHAR(20) NOT NULL CHECK (level IN ('kg', 'nursery', 'primary', 'jss', 'sss')),
    arm_letter VARCHAR(1), -- 'A', 'B', 'C', 'D' (nullable for levels without arms)
    stream VARCHAR(20) CHECK (stream IN ('science', 'technical', 'commercial', 'arts')), -- Only for SSS
    academic_year VARCHAR(20) NOT NULL, -- e.g., "2024/2025"
    capacity INTEGER NOT NULL, -- Max students (15, 20, 25, or 30)
    current_count INTEGER DEFAULT 0, -- Current enrolled students
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, academic_year)
);

CREATE INDEX idx_classes_level ON classes(level);
CREATE INDEX idx_classes_academic_year ON classes(academic_year);
CREATE INDEX idx_classes_stream ON classes(stream) WHERE stream IS NOT NULL;
```

**Class Naming Convention:**

- Format: `{LEVEL} {YEAR}{ARM}` (e.g., "KG 1A", "PRY 3B", "JSS 2C", "SSS 1A")
- Stream is derived from arm for SSS: A=Science, B=Technical, C=Commercial, D=Arts

#### 6. **subjects** (Subject catalog)

```sql
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL, -- e.g., "MTH101", "NUM001"
    level VARCHAR(20) NOT NULL CHECK (level IN ('kg', 'nursery', 'primary', 'jss', 'sss')),
    stream VARCHAR(20) CHECK (stream IN ('science', 'technical', 'commercial', 'arts')), -- Only for SSS subjects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subjects_level ON subjects(level);
CREATE INDEX idx_subjects_stream ON subjects(stream) WHERE stream IS NOT NULL;
```

#### 7. **class_subjects** (Many-to-Many: Classes ↔ Subjects)

```sql
CREATE TABLE class_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, subject_id)
);

CREATE INDEX idx_class_subjects_class ON class_subjects(class_id);
CREATE INDEX idx_class_subjects_subject ON class_subjects(subject_id);
```

#### 8. **staff_subject_assignments** (Many-to-Many: Staff ↔ Subjects ↔ Classes)

```sql
CREATE TABLE staff_subject_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID NOT NULL REFERENCES users(id), -- Admin who assigned
    UNIQUE(staff_id, subject_id, class_id)
);

CREATE INDEX idx_staff_assignments_staff ON staff_subject_assignments(staff_id);
CREATE INDEX idx_staff_assignments_class ON staff_subject_assignments(class_id);
```

#### 9. **class_form_teachers** (Form teacher assignments)

```sql
CREATE TABLE class_form_teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID NOT NULL REFERENCES users(id), -- Admin
    UNIQUE(class_id, staff_id)
);

CREATE INDEX idx_form_teachers_class ON class_form_teachers(class_id);
CREATE INDEX idx_form_teachers_staff ON class_form_teachers(staff_id);
```

#### 10. **enrollment_requests** (Public enrollment submissions)

```sql
CREATE TABLE enrollment_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    parent_name VARCHAR(255) NOT NULL,
    parent_phone VARCHAR(20) NOT NULL,
    parent_email VARCHAR(255),
    requested_class_id UUID NOT NULL REFERENCES classes(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    token VARCHAR(255) UNIQUE, -- For public status lookup
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by UUID REFERENCES users(id) -- Admin
);

CREATE INDEX idx_enrollment_status ON enrollment_requests(status);
CREATE INDEX idx_enrollment_token ON enrollment_requests(token);
```

#### 11. **assignments** (Staff-created assignments)

```sql
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    subject_id UUID NOT NULL REFERENCES subjects(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    created_by UUID NOT NULL REFERENCES users(id), -- Staff member
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assignments_class ON assignments(class_id);
CREATE INDEX idx_assignments_created_by ON assignments(created_by);
```

#### 12. **assignment_submissions** (Student submissions)

```sql
CREATE TABLE assignment_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    response TEXT,
    file_url TEXT, -- Optional file attachment URL
    status VARCHAR(20) DEFAULT 'submitted' CHECK (status IN ('submitted', 'seen')),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    seen_at TIMESTAMP,
    UNIQUE(assignment_id, student_id)
);

CREATE INDEX idx_submissions_assignment ON assignment_submissions(assignment_id);
CREATE INDEX idx_submissions_student ON assignment_submissions(student_id);
```

#### 13. **results** (Student results by term)

```sql
CREATE TABLE results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    academic_year VARCHAR(20) NOT NULL,
    term VARCHAR(20) NOT NULL CHECK (term IN ('first', 'second', 'third')),
    level VARCHAR(20) NOT NULL CHECK (level IN ('kg', 'nursery', 'primary', 'jss', 'sss')),

    -- For KG, Nursery, Primary: 1 CA (40 max) + Exam (60 max)
    ca_score DECIMAL(5,2), -- Nullable, only for kg/nursery/primary
    exam_score DECIMAL(5,2) NOT NULL,

    -- For JSS, SSS: 2 CAs (20 each) + Exam (60)
    first_ca DECIMAL(5,2), -- Nullable, only for jss/sss
    second_ca DECIMAL(5,2), -- Nullable, only for jss/sss

    total_score DECIMAL(5,2) NOT NULL, -- Calculated
    grade VARCHAR(2) NOT NULL, -- A, B, C, D, F

    uploaded_by UUID NOT NULL REFERENCES users(id), -- Staff member
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(student_id, subject_id, academic_year, term)
);

CREATE INDEX idx_results_student ON results(student_id);
CREATE INDEX idx_results_class ON results(class_id);
CREATE INDEX idx_results_academic_year ON results(academic_year);
CREATE INDEX idx_results_term ON results(term);
CREATE INDEX idx_results_subject ON results(subject_id);
```

#### 14. **announcements** (School announcements)

```sql
CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    header VARCHAR(255) NOT NULL,
    about VARCHAR(500), -- Short description
    message TEXT NOT NULL,
    author_id UUID NOT NULL REFERENCES users(id), -- Admin
    audience VARCHAR(20) NOT NULL CHECK (audience IN ('staff', 'students', 'both')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_announcements_audience ON announcements(audience);
CREATE INDEX idx_announcements_created ON announcements(created_at);
```

#### 15. **student_promotions** (Audit trail for promotions)

```sql
CREATE TABLE student_promotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    from_class_id UUID NOT NULL REFERENCES classes(id),
    to_class_id UUID NOT NULL REFERENCES classes(id),
    academic_year VARCHAR(20) NOT NULL,
    promoted_by UUID NOT NULL REFERENCES users(id), -- Admin
    promoted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_promotions_student ON student_promotions(student_id);
```

#### 16. **school_id_sequences** (For atomic ID generation)

```sql
CREATE TABLE school_id_sequences (
    id SERIAL PRIMARY KEY,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'staff')),
    year INTEGER NOT NULL,
    last_number INTEGER DEFAULT 0,
    UNIQUE(role, year)
);

CREATE INDEX idx_sequences_role_year ON school_id_sequences(role, year);
```

---

## ID Generation Service (Concurrency-Safe)

### Implementation

```python
# backend/app/services/id_generator.py

from sqlalchemy import text
from app.database import get_db

def generate_school_id(role: str, enrollment_year: int, db) -> str:
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
        text("""
            INSERT INTO school_id_sequences (role, year, last_number)
            VALUES (:role, :year, 0)
            ON CONFLICT (role, year)
            DO UPDATE SET last_number = school_id_sequences.last_number + 1
            RETURNING last_number
        """),
        {"role": role, "year": enrollment_year}
    )

    next_number = result.scalar()
    unique_id = f"{next_number:04d}"  # Format as 0001, 0002, etc.

    return f"{prefix}/{year}/{unique_id}"

# Preview endpoint (optional, for admin UI)
# GET /api/admin/id-preview?role=student&year=2025
```

---

## File Upload System (Passport Photos)

### Design

**Storage:** Supabase Storage (recommended for MVP) or AWS S3 / DigitalOcean Spaces

**Flow:**

1. Frontend requests presigned upload URL from backend
2. Frontend uploads file directly to storage (bypasses backend)
3. Frontend notifies backend with file URL to attach to profile

**Permissions:**

- Only **Admins** can create/update student/staff profiles (including photos)
- **Staff** and **Students** can view their profile data and photo (read-only in UI)

**Security:**

- File size limit: ≤ 2MB
- Allowed types: `image/jpeg`, `image/png`
- Virus scanning (optional, for production)

### API Endpoints

```
POST   /api/uploads/presign              - Get presigned upload URL
POST   /api/admin/staff/{id}/upload-photo - Attach photo to staff profile
POST   /api/admin/students/{id}/upload-photo - Attach photo to student profile
GET    /api/uploads/{file_path}          - Get file (with auth check)
```

### Implementation

```python
# backend/app/services/upload_service.py

from supabase import create_client, Client
from app.config import settings
import uuid

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

async def get_presigned_upload_url(
    file_name: str,
    file_type: str,
    user_id: str
) -> dict:
    """
    Generate presigned URL for direct client upload

    Returns:
        {
            "upload_url": "https://...",
            "file_path": "photos/staff/...",
            "expires_in": 300
        }
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png"]
    if file_type not in allowed_types:
        raise ValueError("Only JPEG and PNG images are allowed")

    # Generate unique file path
    file_path = f"photos/{user_id}/{uuid.uuid4()}.{file_name.split('.')[-1]}"

    # Generate presigned URL (Supabase example)
    response = supabase.storage.from_("passports").create_signed_upload_url(
        file_path,
        expires_in=300  # 5 minutes
    )

    return {
        "upload_url": response["signedURL"],
        "file_path": file_path,
        "expires_in": 300
    }

async def attach_photo_to_profile(
    user_id: str,
    file_path: str,
    profile_type: str  # 'student' or 'staff'
) -> dict:
    """
    Attach uploaded photo URL to user profile
    """
    photo_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/passports/{file_path}"

    if profile_type == "student":
        # Update student_profiles.photo_url
        pass
    else:
        # Update staff_profiles.photo_url
        pass

    return {"photo_url": photo_url}
```

---

## Result PDF Template & Generation

### PDF Requirements

**Content:**

- School header (logo, name, address)
- Student details block (photo, name, school_id, class, DOB, gender)
- Term & academic year
- Results table: Subject | CA | Exam | Total | Grade
- Summary: Total average, Position in class, Remark, Promoted to (if applicable)
- Footer: Teacher signature line | Date | School stamp/watermark

### Template Structure

```html
<!-- backend/app/templates/result_pdf.html -->
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <style>
      /* Tailwind-compatible CSS for WeasyPrint */
      @page {
        size: A4;
        margin: 20mm;
      }
      .header {
        display: flex;
        justify-content: space-between;
      }
      .student-info {
        display: flex;
        margin: 20px 0;
      }
      .photo {
        width: 100px;
        height: 120px;
        border: 1px solid #ccc;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
      }
      th,
      td {
        border: 1px solid #000;
        padding: 8px;
        text-align: left;
      }
      .summary {
        margin-top: 30px;
      }
      .footer {
        margin-top: 50px;
        display: flex;
        justify-content: space-between;
      }
    </style>
  </head>
  <body>
    <div class="header">
      <div>
        <img src="{{ school_logo_url }}" alt="School Logo" width="80" />
      </div>
      <div>
        <h1>Kristobell Schools</h1>
        <p>Address line here</p>
      </div>
      <div>
        <p><strong>Term:</strong> {{ term }}</p>
        <p><strong>Academic Year:</strong> {{ academic_year }}</p>
      </div>
    </div>

    <div class="student-info">
      <div>
        <img src="{{ student_photo_url }}" alt="Student Photo" class="photo" />
      </div>
      <div>
        <p><strong>Name:</strong> {{ student_name }}</p>
        <p><strong>School ID:</strong> {{ school_id }}</p>
        <p><strong>Class:</strong> {{ class_name }}</p>
        <p><strong>Date of Birth:</strong> {{ date_of_birth }}</p>
        <p><strong>Gender:</strong> {{ gender }}</p>
      </div>
    </div>

    <table>
      <thead>
        <tr>
          <th>Subject</th>
          <th>CA</th>
          <th>Exam</th>
          <th>Total</th>
          <th>Grade</th>
        </tr>
      </thead>
      <tbody>
        {% for result in results %}
        <tr>
          <td>{{ result.subject_name }}</td>
          <td>{{ result.ca_score or result.first_ca + result.second_ca }}</td>
          <td>{{ result.exam_score }}</td>
          <td>{{ result.total_score }}</td>
          <td>{{ result.grade }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    <div class="summary">
      <p><strong>Total Average:</strong> {{ total_average }}</p>
      <p><strong>Position in Class:</strong> {{ position }}</p>
      <p><strong>Remark:</strong> {{ remark }}</p>
      {% if promoted_to %}
      <p><strong>Promoted to:</strong> {{ promoted_to }}</p>
      {% endif %}
    </div>

    <div class="footer">
      <div>
        <p>_____________________</p>
        <p>Teacher's Signature</p>
      </div>
      <div>
        <p>Date: {{ current_date }}</p>
      </div>
      <div>
        <p>School Stamp</p>
      </div>
    </div>
  </body>
</html>
```

### PDF Generation Service

```python
# backend/app/services/pdf_service.py

from weasyprint import HTML
from jinja2 import Template
import io
from datetime import datetime
from app.config import settings
from app.database import get_student_with_profile, get_student_results, calculate_class_ranking

async def generate_result_pdf(
    student_id: str,
    term: str,
    academic_year: str,
    db
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
        current_date=datetime.now().strftime("%Y-%m-%d")
    )

    # Generate PDF
    pdf_bytes = HTML(string=html_content).write_pdf()

    return pdf_bytes
```

### API Endpoints

```
GET    /api/student/results/{term}/download - Download student's result PDF
GET    /api/admin/results/{student_id}/term/{term}/pdf - Admin view/download
GET    /api/admin/class/{class_id}/results/export - Export class results (CSV/XLSX)
GET    /api/staff/results/class/{class_id}/export - Staff export class results
```

---

## API Endpoints Structure (Updated)

### Authentication Routes

```
POST   /api/auth/admin/login          - Admin login (email + password)
POST   /api/auth/staff/login          - Staff login (school_id + password)
POST   /api/auth/student/login        - Student login (school_id + password)
POST   /api/auth/logout               - Logout (all roles)
POST   /api/auth/refresh              - Refresh JWT token
GET    /api/auth/me                   - Get current user info
POST   /api/auth/forgot-password      - Request password reset
POST   /api/auth/reset-password       - Reset password with token
```

### Admin Routes

```
# Staff Management
GET    /api/admin/staff               - List all staff (paginated)
POST   /api/admin/staff               - Create staff
GET    /api/admin/staff/{id}          - Get staff details
PUT    /api/admin/staff/{id}          - Update staff
DELETE /api/admin/staff/{id}          - Delete staff (soft delete)
POST   /api/admin/staff/{id}/assign-subjects - Assign subjects to staff
POST   /api/admin/staff/{id}/upload-photo - Upload staff passport

# Student Management
GET    /api/admin/students            - List all students (paginated)
POST   /api/admin/students            - Create student directly
GET    /api/admin/students/{id}       - Get student details
PUT    /api/admin/students/{id}       - Update student
DELETE /api/admin/students/{id}       - Delete student (soft delete)
POST   /api/admin/students/{id}/promote - Promote student to next class
POST   /api/admin/students/{id}/upload-photo - Upload student passport

# Enrollment Management
GET    /api/admin/enrollments         - List enrollment requests
GET    /api/admin/enrollments/{id}    - Get enrollment details
POST   /api/admin/enrollments/{id}/approve - Approve enrollment
POST   /api/admin/enrollments/{id}/reject - Reject enrollment

# Class Management
GET    /api/admin/classes             - List all classes
POST   /api/admin/classes             - Create class
GET    /api/admin/classes/{id}        - Get class details
PUT    /api/admin/classes/{id}        - Update class
DELETE /api/admin/classes/{id}       - Delete class
POST   /api/admin/classes/{id}/assign-form-teacher - Assign form teacher
GET    /api/admin/classes/{id}/students - Get students in class

# Subject Management
GET    /api/admin/subjects            - List all subjects
POST   /api/admin/subjects            - Create subject
GET    /api/admin/subjects/{id}      - Get subject details
PUT    /api/admin/subjects/{id}      - Update subject
DELETE /api/admin/subjects/{id}      - Delete subject

GET    /api/admin/subject-groups     - List subject groups
POST   /api/admin/subject-groups     - Create subject group

# Announcements
GET    /api/admin/announcements      - List all announcements
POST   /api/admin/announcements      - Create announcement
GET    /api/admin/announcements/{id} - Get announcement
PUT    /api/admin/announcements/{id} - Update announcement
DELETE /api/admin/announcements/{id} - Delete announcement

# Results Management
GET    /api/admin/results            - List all results (with filters)
GET    /api/admin/results/rankings  - Get student rankings
GET    /api/admin/results/class/{class_id} - Get class results
GET    /api/admin/results/{student_id}/term/{term}/pdf - Get result PDF
GET    /api/admin/class/{class_id}/results/export - Export class results (CSV/XLSX)

# File Uploads
POST   /api/uploads/presign          - Get presigned upload URL
GET    /api/admin/id-preview         - Preview next school ID
```

### Staff Routes

```
# Dashboard
GET    /api/staff/dashboard           - Get dashboard data

# Profile (Read-only)
GET    /api/staff/profile             - Get own profile (read-only)

# Assignments
GET    /api/staff/assignments         - List assignments created by staff
POST   /api/staff/assignments         - Create assignment
GET    /api/staff/assignments/{id}    - Get assignment details
PUT    /api/staff/assignments/{id}    - Update assignment
DELETE /api/staff/assignments/{id}    - Delete assignment
GET    /api/staff/assignments/{id}/submissions - Get submissions for assignment
POST   /api/staff/assignments/{id}/submissions/{submission_id}/mark-seen - Mark submission as seen

# Results
GET    /api/staff/results             - List results uploaded by staff
POST   /api/staff/results             - Upload/create result (single or bulk CSV)
PUT    /api/staff/results/{id}        - Update result
GET    /api/staff/results/class/{class_id} - Get results for class
GET    /api/staff/results/class/{class_id}/export - Export class results

# Form Teacher Specific
GET    /api/staff/form-class          - Get assigned form class (if form teacher)
GET    /api/staff/form-class/students - Get students in form class
GET    /api/staff/form-class/results  - Get results for form class
```

### Student Routes

```
# Dashboard
GET    /api/student/dashboard         - Get dashboard data

# Profile (Read-only)
GET    /api/student/profile           - Get own profile (read-only)

# Assignments
GET    /api/student/assignments       - List assignments for student's class
GET    /api/student/assignments/{id}  - Get assignment details
POST   /api/student/assignments/{id}/submit - Submit assignment

# Results
GET    /api/student/results            - Get student's results
GET    /api/student/results/{term}    - Get results for specific term
GET    /api/student/results/{term}/download - Download result PDF

# Announcements
GET    /api/student/announcements      - Get announcements for students
```

### Public Routes

```
POST   /api/public/enrollment         - Submit enrollment request
GET    /api/public/enrollment/{token} - Check enrollment status (with token)
```

---

## Frontend Structure (Detailed)

### Tech Stack

- **Next.js 14+ (App Router)** with TypeScript
- **React Query (TanStack Query)** for server state
- **Zustand** for client state
- **Tailwind CSS** for styling
- **React Hook Form** for forms
- **Axios** for HTTP requests

### Route Structure

#### Public Routes

```
/                                    - Landing page
  - Hero section
  - About school
  - Features
  - Links to portals
  - Enrollment CTA

/enroll                              - Public enrollment form
  - Form with validation
  - CAPTCHA (optional)
  - Success message with token
```

#### Authentication Routes

```
/portal/login                        - Combined login (role selector)
  OR
/portal/admin/login                  - Admin login
/portal/staff/login                  - Staff login
/portal/student/login                - Student login

/portal/forgot-password              - Password reset request
/portal/reset-password               - Password reset form
```

#### Admin Portal Routes

```
/portal/admin/dashboard              - Key metrics (students by level, pending enrollments)
/portal/admin/staff                 - Staff list with create/edit modals
/portal/admin/students              - Student list with create/edit modals
/portal/admin/classes               - Class management (list, create, edit, student counts)
/portal/admin/subjects              - Subject management
/portal/admin/results               - Results search, filter, export
/portal/admin/enrollments           - Enrollment request management
/portal/admin/announcements         - Announcement management
/portal/admin/uploads               - Bulk imports, photo management
```

#### Staff Portal Routes

```
/portal/staff/dashboard              - Dashboard (assignments, form class if applicable)
/portal/staff/assignments           - Create + view submissions
  - /portal/staff/assignments/new
  - /portal/staff/assignments/:id
/portal/staff/results               - Upload results (CSV form or manual entry)
  - /portal/staff/results/upload
/portal/staff/form-class            - Form class management (if form teacher)
```

#### Student Portal Routes

```
/portal/student/dashboard            - View announcements, assignments, results summary
/portal/student/assignments         - List assignments, submit
  - /portal/student/assignments/:id
/portal/student/results             - View results, download PDF
```

### Shared UI Components

```
components/
  common/
    - Header.tsx                    - Top navigation
    - Sidebar.tsx                   - Side navigation (role-based)
    - DataTable.tsx                 - Reusable table with pagination
    - Modal.tsx                     - Modal dialog
    - FormField.tsx                 - Form input wrapper
    - Avatar.tsx                    - User avatar with photo
    - FileUploader.tsx              - File upload component
    - ResultTable.tsx              - Results display table
    - PDFPreview.tsx                - PDF viewer
    - LoadingSpinner.tsx
    - ErrorBoundary.tsx
  admin/
    - StaffForm.tsx
    - StudentForm.tsx
    - ClassForm.tsx
    - EnrollmentCard.tsx
  staff/
    - AssignmentForm.tsx
    - ResultUploadForm.tsx
    - CSVUploader.tsx
  student/
    - AssignmentCard.tsx
    - ResultCard.tsx
```

### Authorization

- **Server-side:** Route protection with middleware
- **Client-side:** Route guards checking JWT + role
- **UI:** Show different navs based on role
- **API:** All endpoints protected with role-based dependencies

### UX Rules

1. **Read-only profiles:** Staff/students see profile info but cannot edit. Show "Request Update" button that sends request to admin.
2. **Inline validation:** Real-time validation for scores (CA ≤ 40, exam ≤ 60, etc.)
3. **CSV import:** Allow staff to upload results via CSV template
4. **Pagination:** All list views paginated (25 items/page default)
5. **Loading states:** Show loading spinners during API calls
6. **Error handling:** User-friendly error messages

---

## Performance & Scaling Considerations

### Database Optimization

**Indexes:**

```sql
-- Already defined in schema, but ensure these exist:
CREATE INDEX idx_users_school_id ON users(school_id);
CREATE INDEX idx_student_profiles_class ON student_profiles(current_class_id);
CREATE INDEX idx_results_student_term ON results(student_id, academic_year, term);
CREATE INDEX idx_classes_level_year ON classes(level, academic_year);
```

**Pagination:**

- Server-side pagination for all list endpoints
- Default page size: 25
- Use cursor-based pagination for large datasets

### Caching Strategy

**Redis (optional for MVP):**

- Cache frequently-read data (class list, subject lists)
- Cache JWT refresh tokens
- Session storage

**Frontend:**

- React Query caching (5-minute default)
- Cache class/subject lists in Zustand

### Background Jobs

**Use Cases:**

- PDF generation for bulk exports
- CSV result imports
- Bulk student promotions
- Email notifications (future)

**Implementation:**

- **Celery** + **Redis** (production)
- **RQ** (simpler alternative)
- For MVP: synchronous PDF generation is acceptable for single requests

### Static Assets

- Serve images from CDN (Supabase Storage + CDN or S3 + CloudFront)
- Optimize images (compress, resize)
- Lazy load images in frontend

### Monitoring & Logging

- **Sentry** for error tracking
- Structured logging (JSON format)
- Log API requests/responses (sanitize sensitive data)
- Monitor database query performance

---

## Security & Privacy

### Authentication

- **JWT tokens:** Short expiration (15 minutes)
- **Refresh tokens:** Stored as HttpOnly Secure cookies
- **Password hashing:** bcrypt (cost factor 12+)
- **Rate limiting:** Public endpoints and login (e.g., 5 requests/minute)

### Authorization

- **RBAC:** Enforce at API dependency level
- **Never trust client-side:** All role checks server-side
- **Principle of least privilege:** Users only access what they need

### Data Protection

- **HTTPS everywhere:** Enforce in production
- **Input validation:** Pydantic schemas for all inputs
- **SQL injection:** Use ORM (SQLAlchemy), never raw SQL
- **XSS prevention:** Sanitize user inputs, use React's built-in escaping
- **CSRF protection:** Use SameSite cookies

### Privacy

- **GDPR considerations:** Store parent contact info securely
- **Data retention:** Soft deletes for audit trail
- **Access logs:** Track who accessed sensitive data
- **Photo storage:** Private buckets, access via presigned URLs

---

## School-Specific Requirements

### School Information

**Mission:** "To provide a nurturing and inclusive environment that challenges students to achieve academic excellence, develop social responsibility and cultivate emotional intelligence"

**Vision:** "To inspire a love for learning and empower students to become confident, compassionate and creative leaders. To raise and nurture spiritually, morally and academically sound children with skills for learning life and work"

**Contact Details:**

- Email: ourrefugeschools@gmail.com
- Mr Ayomide Ojutalayo: 08069292024
- Mrs Ajibola Omoniyi: 08066690070
- Mrs Esther Akindipe: 08143350364

### Grading System

**KG, Nursery & Primary Levels:**

- 1 CA (Continuous Assessment): 40 marks maximum
- Exam: 60 marks maximum
- **Total: 100 marks**

**JSS & SSS Levels:**

- First CA: 20 marks maximum
- Second CA: 20 marks maximum
- Exam: 60 marks maximum
- **Total: 100 marks**

**Grade Scale:**

- A: 70-100
- B: 60-69
- C: 50-59
- D: 40-49
- F: 0-39

### Complete Subject Lists by Level

[Keep all the detailed subject lists from the original plan - they're comprehensive and valuable]

---

## Initial Data Seeding

### Pre-populate Classes

```python
# backend/app/services/seed_classes.py

CLASS_STRUCTURE = {
    'kg': [
        {'name': 'KG 1A', 'capacity': 15},
        {'name': 'KG 1B', 'capacity': 15},
        {'name': 'KG 2A', 'capacity': 15},
        {'name': 'KG 2B', 'capacity': 15},
    ],
    'nursery': [
        {'name': 'NUR 1A', 'capacity': 20},
        {'name': 'NUR 1B', 'capacity': 20},
        {'name': 'NUR 2A', 'capacity': 20},
        {'name': 'NUR 2B', 'capacity': 20},
    ],
    'primary': [
        {'name': 'PRY 1A', 'capacity': 25},
        {'name': 'PRY 1B', 'capacity': 25},
        {'name': 'PRY 1C', 'capacity': 25},
        # ... up to PRY 5C (15 total)
    ],
    'jss': [
        {'name': 'JSS 1A', 'capacity': 30},
        {'name': 'JSS 1B', 'capacity': 30},
        {'name': 'JSS 1C', 'capacity': 30},
        {'name': 'JSS 1D', 'capacity': 30},
        # ... up to JSS 3D (12 total)
    ],
    'sss': [
        {'name': 'SSS 1A', 'capacity': 30, 'stream': 'science'},
        {'name': 'SSS 1B', 'capacity': 30, 'stream': 'technical'},
        {'name': 'SSS 1C', 'capacity': 30, 'stream': 'commercial'},
        {'name': 'SSS 1D', 'capacity': 30, 'stream': 'arts'},
        # ... up to SSS 3D (12 total)
    ],
}
```

### Pre-populate Subjects

[Keep the subject seeding logic from original plan]

---

## Development Phases (Updated)

### Phase 1: Foundation (Week 1-2)

- [ ] Set up FastAPI project structure
- [ ] Set up PostgreSQL database
- [ ] Create database models (consolidated schema)
- [ ] Set up Alembic migrations
- [ ] Set up authentication (JWT + refresh tokens)
- [ ] Create basic API structure
- [ ] Set up Next.js frontend project
- [ ] Create landing page
- [ ] Set up file storage (Supabase Storage)

### Phase 2: Core Features (Week 3-4)

- [ ] User authentication (all roles)
- [ ] ID generation system (DB sequences)
- [ ] Admin: Staff management (CRUD + photo upload)
- [ ] Admin: Student management (CRUD + photo upload)
- [ ] Enrollment system
- [ ] Basic dashboards
- [ ] Profile read-only views

### Phase 3: Academic Features (Week 5-6)

- [ ] Class management (47 classes with capacity tracking)
- [ ] Subject management
- [ ] Assignment system
- [ ] Result management (upload, calculation, validation)
- [ ] Announcements

### Phase 4: Advanced Features (Week 7-8)

- [ ] Form teacher features
- [ ] Result ranking and sorting
- [ ] Student promotion system
- [ ] PDF generation (result sheets)
- [ ] CSV export/import for results
- [ ] Advanced filtering and search

### Phase 5: Polish & Testing (Week 9-10)

- [ ] UI/UX improvements
- [ ] Error handling & validation
- [ ] Performance optimization (indexes, caching)
- [ ] Testing (unit + integration)
- [ ] Documentation
- [ ] Deployment preparation

---

## Color Scheme Implementation

```javascript
// frontend/src/utils/constants.ts
export const COLORS = {
  primary: "#08253F", // Primary Dark Blue
  secondary: "#DA0F00", // Secondary Red
  accent: "#6A89A5", // Accent Blue-Grey
};
```

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        "Kristobell-primary": "#08253F",
        "Kristobell-secondary": "#DA0F00",
        "Kristobell-accent": "#6A89A5",
      },
    },
  },
};
```

---

## Next Steps

1. **Initialize the project**

   - Create backend and frontend folders
   - Set up virtual environment
   - Install dependencies
   - Set up Git repository

2. **Database setup**

   - Create PostgreSQL database
   - Run initial Alembic migration
   - Seed classes and subjects

3. **Build authentication first**

   - This is the foundation for everything else

4. **Implement one feature at a time**

   - Start with Admin features
   - Then Staff features
   - Finally Student features

5. **Test incrementally**
   - Write tests as you build
   - Test with realistic data volumes

---

## Notes on "Senior Dev Thinking"

The comment "You already think like a senior dev — you just need execution discipline" refers to:

1. **System thinking:** You're considering the full system (database, API, frontend) holistically
2. **Scalability awareness:** You're thinking about 500+ students, multiple classes, performance
3. **User experience:** You're considering different user roles and their needs
4. **Real-world constraints:** You understand school operations (enrollment, results, promotions)

**What "execution discipline" means:**

- Breaking down the big picture into small, manageable tasks
- Building incrementally (MVP first)
- Testing as you go
- Not getting overwhelmed by the scope
- Shipping working features, not perfect code

This plan helps with execution discipline by providing clear phases, specific endpoints, and concrete implementation steps.
