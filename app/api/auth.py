"""
POST   /api/auth/admin/login          - Admin login (email + password)
POST   /api/auth/staff/login          - Staff login (school_id + password)
POST   /api/auth/student/login        - Student login (school_id + password)
POST   /api/auth/logout               - Logout (all roles)
POST   /api/auth/refresh              - Refresh JWT token
GET    /api/auth/me                   - Get current user info
POST   /api/auth/forgot-password      - Request password reset
POST   /api/auth/reset-password       - Reset password with token
"""

from fastapi import APIRouter


router = APIRouter(prefix="/api/auth", tags=["Authentication"])
