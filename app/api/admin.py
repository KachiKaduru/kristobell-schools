"""
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
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["Admin"])
