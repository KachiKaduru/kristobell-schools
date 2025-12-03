"""
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
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/staff", tags=["Staff"])
