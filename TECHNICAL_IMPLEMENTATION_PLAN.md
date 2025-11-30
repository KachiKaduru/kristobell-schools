# Kristobell School Management System - Technical Implementation Plan

## Tech Stack Recommendation

### Backend

- **FastAPI** - Modern Python web framework (you're learning this!)
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** or **SQLite** (for development) - Database
- **Pydantic** - Data validation (comes with FastAPI)
- **JWT** (python-jose) - Authentication tokens
- **Passlib** + **bcrypt** - Password hashing
- **Alembic** - Database migrations

### Frontend

- **React** or **Next.js** (if you want SSR) - UI framework
- **React Router** - Client-side routing
- **Axios** or **Fetch API** - HTTP requests
- **Context API** or **Redux/Zustand** - State management
- **Tailwind CSS** or **Styled Components** - Styling

### Additional Tools

- **Docker** (optional) - Containerization
- **Git** - Version control

---

## System Architecture

```
┌─────────────────┐
│  Landing Page   │  (Public - React/Next.js)
└────────┬────────┘
         │
         ├─── Admin Portal Login
         ├─── Staff Portal Login
         └─── Student Portal Login
                │
                ▼
┌─────────────────────────────────┐
│      FastAPI Backend            │
│  ┌───────────────────────────┐  │
│  │  Authentication Service   │  │
│  │  - JWT Token Generation   │  │
│  │  - Role-based Auth        │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Business Logic Services  │  │
│  │  - ID Generation          │  │
│  │  - Result Calculation     │  │
│  │  - Enrollment Processing  │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  API Routes (REST)        │  │
│  └───────────────────────────┘  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────┐
│    PostgreSQL Database      │
└─────────────────────────────┘
```

---

## Database Schema Design

### Core Tables

#### 1. **users** (Base table for all user types)

```sql
- id (UUID, Primary Key)
- email (String, Unique, Nullable - for Admin only)
- school_id (String, Unique, Nullable - for Staff/Students)
- password_hash (String)
- role (Enum: 'admin', 'staff', 'student')
- is_active (Boolean)
- created_at (Timestamp)
- updated_at (Timestamp)
```

#### 2. **admins**

```sql
- id (UUID, Primary Key, Foreign Key → users.id)
- full_name (String)
- email (String, Unique)
- phone (String, Nullable)
- created_at (Timestamp)
```

#### 3. **staff**

```sql
- id (UUID, Primary Key, Foreign Key → users.id)
- school_id (String, Unique) -- Kristobell/STF/YYYY/UniqueID
- full_name (String)
- phone (String)
- date_of_birth (Date, Nullable)
- employment_date (Date)
- is_form_teacher (Boolean, Default: False)
- created_at (Timestamp)
```

#### 4. **students**

```sql
- id (UUID, Primary Key, Foreign Key → users.id)
- school_id (String, Unique) -- Kristobell/STU/YYYY/UniqueID
- full_name (String)
- date_of_birth (Date)
- gender (Enum)
- parent_name (String)
- parent_phone (String)
- parent_email (String, Nullable)
- enrollment_year (Integer) -- YYYY from school_id
- enrollment_status (Enum: 'pending', 'approved', 'rejected')
- current_class_id (UUID, Foreign Key → classes.id, Nullable)
- created_at (Timestamp)
```

#### 5. **enrollment_requests**

```sql
- id (UUID, Primary Key)
- student_id (UUID, Foreign Key → students.id)
- full_name (String)
- date_of_birth (Date)
- gender (Enum)
- parent_name (String)
- parent_phone (String)
- parent_email (String)
- requested_class_id (UUID, Foreign Key → classes.id)
- status (Enum: 'pending', 'approved', 'rejected')
- admin_notes (Text, Nullable)
- created_at (Timestamp)
- reviewed_at (Timestamp, Nullable)
- reviewed_by (UUID, Foreign Key → admins.id, Nullable)
```

#### 6. **classes**

```sql
- id (UUID, Primary Key)
- name (String) -- e.g., "JSS 1A", "SSS 2 Science", "KG 1A"
- level (Enum: 'kg', 'nursery', 'primary', 'jss', 'sss')
- stream (Enum: 'science', 'commercial', 'arts', Nullable) -- Only for SSS level
- academic_year (String) -- e.g., "2024/2025"
- max_students (Integer, Nullable)
- created_at (Timestamp)
```

#### 7. **class_form_teachers** (Many-to-Many: Classes ↔ Staff)

```sql
- id (UUID, Primary Key)
- class_id (UUID, Foreign Key → classes.id)
- staff_id (UUID, Foreign Key → staff.id)
- assigned_at (Timestamp)
- assigned_by (UUID, Foreign Key → admins.id)
- UNIQUE(class_id, staff_id)
```

#### 8. **subject_groups**

```sql
- id (UUID, Primary Key)
- name (String) -- e.g., "SS Science", "SS Commerce", "JSS", "KG/Nursery 1"
- description (Text, Nullable)
- level (Enum: 'kg', 'nursery', 'primary', 'jss', 'sss')
- stream (Enum: 'science', 'commercial', 'arts', Nullable) -- Only for SSS groups
- created_at (Timestamp)
```

#### 9. **subjects**

```sql
- id (UUID, Primary Key)
- name (String)
- code (String, Unique) -- e.g., "MTH101", "NUM001" (for Number work)
- subject_group_id (UUID, Foreign Key → subject_groups.id, Nullable)
- level (Enum: 'kg', 'nursery', 'primary', 'jss', 'sss')
- created_at (Timestamp)
```

#### 10. **class_subjects** (Many-to-Many: Classes ↔ Subjects)

```sql
- id (UUID, Primary Key)
- class_id (UUID, Foreign Key → classes.id)
- subject_id (UUID, Foreign Key → subjects.id)
- UNIQUE(class_id, subject_id)
```

#### 11. **staff_subject_assignments** (Many-to-Many: Staff ↔ Subjects ↔ Classes)

```sql
- id (UUID, Primary Key)
- staff_id (UUID, Foreign Key → staff.id)
- subject_id (UUID, Foreign Key → subjects.id)
- class_id (UUID, Foreign Key → classes.id)
- assigned_at (Timestamp)
- assigned_by (UUID, Foreign Key → admins.id)
- UNIQUE(staff_id, subject_id, class_id)
```

#### 12. **announcements**

```sql
- id (UUID, Primary Key)
- header (String)
- about (String) -- Short description
- message (Text)
- author_id (UUID, Foreign Key → admins.id)
- audience (Enum: 'staff', 'students', 'both')
- created_at (Timestamp)
- updated_at (Timestamp)
```

#### 13. **assignments**

```sql
- id (UUID, Primary Key)
- title (String)
- description (Text)
- subject_id (UUID, Foreign Key → subjects.id)
- class_id (UUID, Foreign Key → classes.id)
- created_by (UUID, Foreign Key → staff.id)
- due_date (Timestamp, Nullable)
- created_at (Timestamp)
- updated_at (Timestamp)
```

#### 14. **assignment_submissions**

```sql
- id (UUID, Primary Key)
- assignment_id (UUID, Foreign Key → assignments.id)
- student_id (UUID, Foreign Key → students.id)
- response (Text)
- status (Enum: 'submitted', 'seen') -- 'seen' when teacher marks it
- submitted_at (Timestamp)
- seen_at (Timestamp, Nullable)
```

#### 15. **results**

```sql
- id (UUID, Primary Key)
- student_id (UUID, Foreign Key → students.id)
- subject_id (UUID, Foreign Key → subjects.id)
- class_id (UUID, Foreign Key → classes.id)
- academic_year (String)
- term (Enum: 'first', 'second', 'third')
- level (Enum: 'kg', 'nursery', 'primary', 'jss', 'sss')

  -- Grading fields based on level
  -- For Nursery & Primary:
  - ca_score (Float) -- 40 max
  - exam_score (Float) -- 60 max
  - total_score (Float) -- Calculated: ca_score + exam_score

  -- For JSS & SSS:
  - first_ca (Float) -- 20 max
  - second_ca (Float) -- 20 max
  - exam_score (Float) -- 60 max
  - total_score (Float) -- Calculated: first_ca + second_ca + exam_score

  - grade (String) -- Calculated based on total_score
  - uploaded_by (UUID, Foreign Key → staff.id)
  - created_at (Timestamp)
  - updated_at (Timestamp)

  UNIQUE(student_id, subject_id, academic_year, term)
```

#### 16. **student_promotions** (Audit trail)

```sql
- id (UUID, Primary Key)
- student_id (UUID, Foreign Key → students.id)
- from_class_id (UUID, Foreign Key → classes.id)
- to_class_id (UUID, Foreign Key → classes.id)
- academic_year (String)
- promoted_by (UUID, Foreign Key → admins.id)
- promoted_at (Timestamp)
```

---

## API Endpoints Structure

### Authentication Routes

```
POST   /api/auth/admin/login          - Admin login (email + password)
POST   /api/auth/staff/login          - Staff login (school_id + password)
POST   /api/auth/student/login        - Student login (school_id + password)
POST   /api/auth/logout               - Logout (all roles)
POST   /api/auth/refresh              - Refresh JWT token
GET    /api/auth/me                   - Get current user info
```

### Admin Routes

```
# Staff Management
GET    /api/admin/staff               - List all staff
POST   /api/admin/staff               - Create staff
GET    /api/admin/staff/{id}          - Get staff details
PUT    /api/admin/staff/{id}          - Update staff
DELETE /api/admin/staff/{id}          - Delete staff
POST   /api/admin/staff/{id}/assign-subjects - Assign subjects to staff

# Student Management
GET    /api/admin/students            - List all students
POST   /api/admin/students            - Create student directly
GET    /api/admin/students/{id}       - Get student details
PUT    /api/admin/students/{id}       - Update student
DELETE /api/admin/students/{id}       - Delete student
POST   /api/admin/students/{id}/promote - Promote student to next class

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
DELETE /api/admin/classes/{id}        - Delete class
POST   /api/admin/classes/{id}/assign-form-teacher - Assign form teacher
GET    /api/admin/classes/{id}/students - Get students in class

# Subject Management
GET    /api/admin/subjects            - List all subjects
POST   /api/admin/subjects            - Create subject
GET    /api/admin/subjects/{id}       - Get subject details
PUT    /api/admin/subjects/{id}       - Update subject
DELETE /api/admin/subjects/{id}       - Delete subject

GET    /api/admin/subject-groups      - List subject groups
POST   /api/admin/subject-groups      - Create subject group

# Announcements
GET    /api/admin/announcements       - List all announcements
POST   /api/admin/announcements       - Create announcement
GET    /api/admin/announcements/{id}  - Get announcement
PUT    /api/admin/announcements/{id}  - Update announcement
DELETE /api/admin/announcements/{id}  - Delete announcement

# Results Management
GET    /api/admin/results             - List all results (with filters)
GET    /api/admin/results/rankings    - Get student rankings
GET    /api/admin/results/class/{class_id} - Get class results
```

### Staff Routes

```
# Dashboard
GET    /api/staff/dashboard           - Get dashboard data

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
POST   /api/staff/results             - Upload/create result
PUT    /api/staff/results/{id}        - Update result
GET    /api/staff/results/class/{class_id} - Get results for class

# Form Teacher Specific
GET    /api/staff/form-class          - Get assigned form class (if form teacher)
GET    /api/staff/form-class/students - Get students in form class
GET    /api/staff/form-class/results  - Get results for form class
```

### Student Routes

```
# Dashboard
GET    /api/student/dashboard         - Get dashboard data

# Assignments
GET    /api/student/assignments       - List assignments for student's class
GET    /api/student/assignments/{id}  - Get assignment details
POST   /api/student/assignments/{id}/submit - Submit assignment

# Results
GET    /api/student/results           - Get student's results
GET    /api/student/results/{term}    - Get results for specific term

# Announcements
GET    /api/student/announcements     - Get announcements for students
```

### Public Routes

```
POST   /api/public/enrollment         - Submit enrollment request
GET    /api/public/enrollment/{id}    - Check enrollment status (with token)
```

---

## Frontend Structure

### Landing Page (Public)

```
/ (Home)
  - Hero section
  - About school
  - Features
  - Links to portals:
    - /portal/admin/login
    - /portal/staff/login
    - /portal/student/login
  - Enrollment form link: /enroll
```

### Portal Routes (Protected)

#### Admin Portal

```
/portal/admin/login
/portal/admin/dashboard
/portal/admin/staff
  - /portal/admin/staff/new
  - /portal/admin/staff/:id
/portal/admin/students
  - /portal/admin/students/new
  - /portal/admin/students/:id
/portal/admin/enrollments
  - /portal/admin/enrollments/:id
/portal/admin/classes
  - /portal/admin/classes/new
  - /portal/admin/classes/:id
/portal/admin/subjects
  - /portal/admin/subjects/new
  - /portal/admin/subjects/:id
/portal/admin/announcements
  - /portal/admin/announcements/new
  - /portal/admin/announcements/:id
/portal/admin/results
```

#### Staff Portal

```
/portal/staff/login
/portal/staff/dashboard
/portal/staff/assignments
  - /portal/staff/assignments/new
  - /portal/staff/assignments/:id
/portal/staff/results
  - /portal/staff/results/upload
/portal/staff/form-class (if form teacher)
```

#### Student Portal

```
/portal/student/login
/portal/student/dashboard
/portal/student/assignments
  - /portal/student/assignments/:id
/portal/student/results
```

---

## Key Technical Components

### 1. ID Generation Service

```python
# Backend service to generate school IDs
def generate_school_id(role: str, enrollment_year: int) -> str:
    """
    Generate unique school ID: Kristobell/STU/YYYY/UniqueID or Kristobell/STF/YYYY/UniqueID

    Args:
        role: 'student' or 'staff'
        enrollment_year: Year of enrollment

    Returns:
        Unique school ID string
    """
    prefix = "Kristobell/STU" if role == "student" else "Kristobell/STF"
    year = str(enrollment_year)

    # Get the last unique ID for this role and year
    last_id = get_last_unique_id(role, enrollment_year)
    next_id = (last_id or 0) + 1

    unique_id = f"{next_id:04d}"  # Format as 0001, 0002, etc.

    return f"{prefix}/{year}/{unique_id}"
```

### 2. Authentication Middleware

```python
# FastAPI dependency for role-based access
def require_role(allowed_roles: List[str]):
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
```

### 3. Result Calculation Logic

```python
def calculate_result(level: str, scores: dict) -> dict:
    """
    Calculate total score and grade based on education level

    Args:
        level: 'nursery', 'primary', 'jss', 'sss'
        scores: Dict with CA and exam scores

    Returns:
        Dict with total_score and grade
    """
    if level in ['nursery', 'primary']:
        total = scores['ca_score'] + scores['exam_score']
    else:  # jss, sss
        total = scores['first_ca'] + scores['second_ca'] + scores['exam_score']

    grade = calculate_grade(total)  # A, B, C, D, F based on ranges

    return {
        'total_score': total,
        'grade': grade
    }
```

### 4. Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

---

## Project File Structure

```
Kristobell-school-management/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Database connection
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── admin.py
│   │   │   ├── staff.py
│   │   │   ├── student.py
│   │   │   ├── class.py
│   │   │   ├── subject.py
│   │   │   ├── assignment.py
│   │   │   ├── result.py
│   │   │   └── announcement.py
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── auth.py
│   │   │   └── ...
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependencies (auth, db)
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── admin.py
│   │   │   │   ├── staff.py
│   │   │   │   ├── student.py
│   │   │   │   └── public.py
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── id_generator.py
│   │   │   ├── result_calculator.py
│   │   │   └── enrollment_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── security.py
│   ├── alembic/                    # Database migrations
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Header.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── Modal.jsx
│   │   │   │   └── Table.jsx
│   │   │   ├── admin/
│   │   │   ├── staff/
│   │   │   └── student/
│   │   ├── pages/
│   │   │   ├── Landing.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── admin/
│   │   │   ├── staff/
│   │   │   └── student/
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx
│   │   ├── services/
│   │   │   └── api.js              # API client
│   │   ├── utils/
│   │   │   └── constants.js        # Color scheme, etc.
│   │   └── App.jsx
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

---

## Development Phases

### Phase 1: Foundation (Week 1-2)

- [ ] Set up FastAPI project structure
- [ ] Set up database (PostgreSQL/SQLite)
- [ ] Create database models
- [ ] Set up authentication (JWT)
- [ ] Create basic API structure
- [ ] Set up frontend project
- [ ] Create landing page

### Phase 2: Core Features (Week 3-4)

- [ ] User authentication (all roles)
- [ ] ID generation system
- [ ] Admin: Staff management
- [ ] Admin: Student management
- [ ] Enrollment system
- [ ] Basic dashboards

### Phase 3: Academic Features (Week 5-6)

- [ ] Class management
- [ ] Subject management
- [ ] Assignment system
- [ ] Result management
- [ ] Announcements

### Phase 4: Advanced Features (Week 7-8)

- [ ] Form teacher features
- [ ] Result ranking and sorting
- [ ] Student promotion system
- [ ] Advanced filtering and search

### Phase 5: Polish & Testing (Week 9-10)

- [ ] UI/UX improvements
- [ ] Error handling
- [ ] Input validation
- [ ] Testing
- [ ] Documentation

---

## Color Scheme Implementation

```javascript
// frontend/src/utils/constants.js
export const COLORS = {
  primary: "#08253F", // Primary Dark Blue
  secondary: "#DA0F00", // Secondary Red
  accent: "#6A89A5", // Accent Blue-Grey
};
```

```css
/* Tailwind config */
module.exports = {
  theme: {
    extend: {
      colors: {
        'Kristobell-primary': '#08253F',
        'Kristobell-secondary': '#DA0F00',
        'Kristobell-accent': '#6A89A5',
      },
    },
  },
};
```

---

## School-Specific Requirements & Subject Lists

### School Information

**Mission:** "To provide a nurturing and inclusive environment that challenges students to achieve academic excellence, develop social responsibility and cultivate emotional intelligence"

**Vision:** "To inspire a love for learning and empower students to become confident, compassionate and creative leaders. To raise and nurture spiritually, morally and academically sound children with skills for learning life and work"

**Contact Details:**

- Email: ourrefugeschools@gmail.com
- Mr Ayomide Ojutalayo: 08069292024
- Mrs Ajibola Omoniyi: 08066690070
- Mrs Esther Akindipe: 08143350364

### Grading System Clarification

**Nursery & Primary Levels:**

- 1 CA (Continuous Assessment): 40 marks maximum
- Exam: 60 marks maximum
- **Total: 100 marks**

**Junior & Senior Secondary Levels:**

- First CA: 20 marks maximum
- Second CA: 20 marks maximum
- Exam: 60 marks maximum
- **Total: 100 marks**

### Education Levels & Class Structure

The system needs to support these education levels:

1. **KG 1, KG 2, Nursery 1** (Early Years)
2. **Nursery 2**
3. **Primary 1 - 5**
4. **Junior Secondary School (JSS) 1 - 3**
5. **Senior Secondary School (SSS)** with streams:
   - Science
   - Commercial
   - Arts

### Complete Subject Lists by Level

#### KG 1, KG 2, and Nursery 1 (13 subjects)

1. Number work
2. Letter work
3. Basic science
4. Social habit
5. Health habit
6. Moral instruction
7. Civic education
8. Rhymes
9. Colouring
10. Current Affairs
11. Phonics
12. Speech training
13. Picture reading

#### Nursery 2 (9 subjects)

1. Mathematics
2. English studies
3. Basic science
4. Basic Technology
5. Home Economics
6. Social studies
7. Agric science
8. Phonics
9. Bible knowledge

#### Primary 1 - 5 (16 subjects)

1. Mathematics
2. English studies
3. Basic science
4. Basic Technology
5. Home Economics
6. Social studies
7. Civic Education
8. Computer
9. History
10. Yoruba
11. Literature in English
12. Bible knowledge
13. Agric science
14. C.C.A. (Creative and Cultural Arts)
15. Phonics
16. P.H.E. (Physical and Health Education)

#### Junior Secondary School (JSS) 1 - 3 (17 subjects)

1. Mathematics
2. English studies
3. Basic science
4. Basic Technology
5. Home Economics
6. Agricultural science
7. Civic Education
8. Business studies
9. Computer studies
10. C.C.A. (Creative and Cultural Arts)
11. Yoruba
12. C.R.S. (Christian Religious Studies)
13. Music
14. Phonics
15. History
16. P.H.E. (Physical and Health Education)
17. Social studies

#### Senior Secondary School - Science Stream (12 subjects)

1. Mathematics
2. English
3. Civic Education
4. Animal Husbandry
5. Biology
6. Chemistry
7. Physics
8. Geography
9. Economics
10. Agricultural science
11. Phonics
12. Yoruba

#### Senior Secondary School - Commercial Stream (12 subjects)

1. Mathematics
2. English
3. Civic Education
4. Animal Husbandry
5. Biology
6. Financial Accounting
7. Commerce
8. Economics
9. Agricultural science
10. Phonics
11. Yoruba
12. Government

#### Senior Secondary School - Arts Stream (12 subjects)

1. Mathematics
2. English
3. Civic Education
4. Animal Husbandry
5. Biology
6. Literature
7. C.R.S. (Christian Religious Studies)
8. Economics
9. Agricultural science
10. Phonics
11. Yoruba
12. Government

### Database Schema Updates for Subjects

The `classes` table needs an additional field for SSS streams:

```sql
-- Update classes table
ALTER TABLE classes ADD COLUMN stream (Enum: 'science', 'commercial', 'arts', NULL)
-- Only applicable for SSS level classes
```

### Subject Group Structure

Subject groups should be organized as:

- **KG/Nursery 1 Group** - For KG 1, KG 2, Nursery 1
- **Nursery 2 Group**
- **Primary Group** - For Primary 1-5
- **JSS Group** - For JSS 1-3
- **SSS Science Group**
- **SSS Commercial Group**
- **SSS Arts Group**

### Additional Features Required

1. **Result Download/Export**

   - Students should be able to download their results (PDF/Excel)
   - Admin should be able to export class results
   - Staff should be able to download results for their classes

2. **No Profile Pages**

   - Staff and students don't need dedicated profile pages
   - User information can be displayed in dashboard headers/sidebars

3. **Admin Classes Page**

   - Dedicated page for managing classes
   - View all classes with student counts
   - Manage class assignments

4. **Admin Results Viewing**

   - Admin should be able to view all results
   - Filter by class, term, academic year
   - View rankings and statistics

5. **Periodic Result Uploading**
   - Support for uploading results by term (First, Second, Third)
   - Track academic year for each result entry

### Result Calculation Service (Updated)

```python
def calculate_result(level: str, scores: dict) -> dict:
    """
    Calculate total score and grade based on education level

    Args:
        level: 'kg', 'nursery', 'primary', 'jss', 'sss'
        scores: Dict with CA and exam scores

    Returns:
        Dict with total_score and grade
    """
    if level in ['kg', 'nursery', 'primary']:
        # 1 CA (40 max) + Exam (60 max) = 100
        ca_score = scores.get('ca_score', 0)
        exam_score = scores.get('exam_score', 0)

        # Validate max scores
        if ca_score > 40:
            raise ValueError("CA score cannot exceed 40 for Nursery/Primary")
        if exam_score > 60:
            raise ValueError("Exam score cannot exceed 60")

        total = ca_score + exam_score
    else:  # jss, sss
        # 2 CAs (20 each) + Exam (60) = 100
        first_ca = scores.get('first_ca', 0)
        second_ca = scores.get('second_ca', 0)
        exam_score = scores.get('exam_score', 0)

        # Validate max scores
        if first_ca > 20 or second_ca > 20:
            raise ValueError("CA scores cannot exceed 20 for Secondary")
        if exam_score > 60:
            raise ValueError("Exam score cannot exceed 60")

        total = first_ca + second_ca + exam_score

    grade = calculate_grade(total)  # A, B, C, D, F based on ranges

    return {
        'total_score': round(total, 2),
        'grade': grade
    }

def calculate_grade(total_score: float) -> str:
    """Calculate letter grade based on total score"""
    if total_score >= 70:
        return 'A'
    elif total_score >= 60:
        return 'B'
    elif total_score >= 50:
        return 'C'
    elif total_score >= 40:
        return 'D'
    else:
        return 'F'
```

### Updated API Endpoints for Result Download

```
# Add to existing endpoints
GET    /api/admin/results/export          - Export results (PDF/Excel)
GET    /api/admin/results/class/{id}/export - Export class results
GET    /api/student/results/download       - Download student's results
GET    /api/staff/results/class/{id}/export - Export class results
```

### Frontend Updates

**Remove:**

- `/portal/staff/profile` - No profile page needed
- `/portal/student/profile` - No profile page needed

**Add:**

- Result download buttons on result viewing pages
- Export functionality for admin results page
- Enhanced classes management page for admin

---

## Initial Data Seeding

### Pre-populate Subjects

When setting up the database, you'll need to seed all subjects for each level. Here's a Python script structure for seeding:

```python
# backend/app/services/seed_subjects.py

SUBJECTS_BY_LEVEL = {
    'kg': [
        'Number work', 'Letter work', 'Basic science', 'Social habit',
        'Health habit', 'Moral instruction', 'Civic education', 'Rhymes',
        'Colouring', 'Current Affairs', 'Phonics', 'Speech training',
        'Picture reading'
    ],
    'nursery': [
        'Mathematics', 'English studies', 'Basic science', 'Basic Technology',
        'Home Economics', 'Social studies', 'Agric science', 'Phonics',
        'Bible knowledge'
    ],
    'primary': [
        'Mathematics', 'English studies', 'Basic science', 'Basic Technology',
        'Home Economics', 'Social studies', 'Civic Education', 'Computer',
        'History', 'Yoruba', 'Literature in English', 'Bible knowledge',
        'Agric science', 'C.C.A.', 'Phonics', 'P.H.E.'
    ],
    'jss': [
        'Mathematics', 'English studies', 'Basic science', 'Basic Technology',
        'Home Economics', 'Agricultural science', 'Civic Education',
        'Business studies', 'Computer studies', 'C.C.A.', 'Yoruba', 'C.R.S.',
        'Music', 'Phonics', 'History', 'P.H.E.', 'Social studies'
    ],
    'sss_science': [
        'Mathematics', 'English', 'Civic Education', 'Animal Husbandry',
        'Biology', 'Chemistry', 'Physics', 'Geography', 'Economics',
        'Agricultural science', 'Phonics', 'Yoruba'
    ],
    'sss_commercial': [
        'Mathematics', 'English', 'Civic Education', 'Animal Husbandry',
        'Biology', 'Financial Accounting', 'Commerce', 'Economics',
        'Agricultural science', 'Phonics', 'Yoruba', 'Government'
    ],
    'sss_arts': [
        'Mathematics', 'English', 'Civic Education', 'Animal Husbandry',
        'Biology', 'Literature', 'C.R.S.', 'Economics', 'Agricultural science',
        'Phonics', 'Yoruba', 'Government'
    ]
}

def generate_subject_code(name: str, level: str) -> str:
    """Generate unique subject code"""
    # Simple implementation - can be enhanced
    prefix_map = {
        'kg': 'KG',
        'nursery': 'NUR',
        'primary': 'PRI',
        'jss': 'JSS',
        'sss': 'SSS'
    }
    prefix = prefix_map.get(level, 'GEN')
    # Create code from first 3 letters of subject name
    name_code = ''.join([c for c in name[:3].upper() if c.isalpha()])
    return f"{prefix}{name_code}001"  # Simplified - should check uniqueness
```

### Subject Group Seeding

```python
SUBJECT_GROUPS = [
    {'name': 'KG/Nursery 1', 'level': 'kg', 'stream': None},
    {'name': 'Nursery 2', 'level': 'nursery', 'stream': None},
    {'name': 'Primary', 'level': 'primary', 'stream': None},
    {'name': 'JSS', 'level': 'jss', 'stream': None},
    {'name': 'SSS Science', 'level': 'sss', 'stream': 'science'},
    {'name': 'SSS Commercial', 'level': 'sss', 'stream': 'commercial'},
    {'name': 'SSS Arts', 'level': 'sss', 'stream': 'arts'},
]
```

---

## Security Considerations

1. **Password Security**

   - Use bcrypt for hashing
   - Enforce password complexity rules
   - Implement password reset functionality

2. **JWT Tokens**

   - Set appropriate expiration times
   - Use refresh tokens
   - Store tokens securely (httpOnly cookies or localStorage)

3. **Role-Based Access Control**

   - Validate roles on every protected endpoint
   - Use middleware to check permissions
   - Never trust client-side role checks

4. **Input Validation**

   - Validate all inputs using Pydantic schemas
   - Sanitize user inputs
   - Prevent SQL injection (use ORM)

5. **CORS Configuration**
   - Configure CORS properly for production
   - Only allow trusted origins

---

## Next Steps

1. **Initialize the project**

   - Create backend and frontend folders
   - Set up virtual environment
   - Install dependencies

2. **Start with database**

   - Design and create tables
   - Set up Alembic for migrations

3. **Build authentication first**

   - This is the foundation for everything else

4. **Implement one feature at a time**
   - Start with Admin features
   - Then Staff features
   - Finally Student features

Would you like me to help you start building this? I can create the initial project structure and set up the FastAPI backend with database models!
