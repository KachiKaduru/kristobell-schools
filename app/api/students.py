"""
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
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/student", tags=["Students"])
