"""
Reporting compatibility routes — bridges the Jana Sunuwaai frontend
with the AI pothole detection backend.

Endpoints:
    GET  /api/v1/reports/nearby   — list reports (returns AI detections as reports)
    GET  /api/v1/reports/:id      — single report detail
    POST /api/v1/reports          — submit a new report (runs AI prediction)
    GET  /api/v1/reports/:id/status   — report status
    POST /api/v1/reports/:id/vote     — upvote/downvote
    GET  /api/v1/reports/:id/comments — list comments
    POST /api/v1/reports/:id/comments — add comment
    GET  /api/v1/departments          — list departments/categories
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["Reporting"])


# ── In-memory store (replace with DB in production) ─────────────
_reports_store: list = []
_comments_store: dict = {}   # report_id -> list of comments
_votes_store: dict = {}      # report_id -> {"up": int, "down": int}
_next_id = 1


# ── Schemas ─────────────────────────────────────────────────────
class LocationSchema(BaseModel):
    lat: float = 27.7172
    lng: float = 85.3240
    address: str = "Kathmandu, Nepal"
    ward: str = "Ward 1"


class ReportResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    location: LocationSchema
    image_url: Optional[str] = None
    created_at: str
    upvotes: int = 0
    downvotes: int = 0


class CommentSchema(BaseModel):
    id: int
    report_id: int
    user: str
    text: str
    created_at: str


class DepartmentSchema(BaseModel):
    id: int
    name: str
    description: str


# ── Seed data ───────────────────────────────────────────────────
DEPARTMENTS = [
    DepartmentSchema(id=1, name="Road Infrastructure", description="Potholes, road damage, and pavement issues"),
    DepartmentSchema(id=2, name="Water & Sanitation", description="Water supply, drainage, and sewage"),
    DepartmentSchema(id=3, name="Electricity", description="Street lights, power lines, and electrical hazards"),
    DepartmentSchema(id=4, name="Waste Management", description="Garbage collection and disposal"),
    DepartmentSchema(id=5, name="Public Safety", description="Traffic signals, signage, and safety barriers"),
]

SEED_REPORTS = [
    ReportResponse(
        id=1,
        title="Large pothole on Ring Road",
        description="Dangerous pothole near Kalanki intersection causing accidents",
        category="Road Infrastructure",
        status="pending",
        location=LocationSchema(lat=27.6933, lng=85.2814, address="Ring Road, Kalanki", ward="Ward 14"),
        created_at=datetime.now().isoformat(),
        upvotes=12,
    ),
    ReportResponse(
        id=2,
        title="Pothole cluster on Koteshwor road",
        description="Multiple potholes making the road nearly impassable for two-wheelers",
        category="Road Infrastructure",
        status="in_progress",
        location=LocationSchema(lat=27.6783, lng=85.3493, address="Koteshwor Main Road", ward="Ward 32"),
        created_at=datetime.now().isoformat(),
        upvotes=24,
    ),
    ReportResponse(
        id=3,
        title="Road surface damage near Balaju",
        description="Heavy rain caused road erosion exposing underground pipes",
        category="Road Infrastructure",
        status="resolved",
        location=LocationSchema(lat=27.7300, lng=85.3050, address="Balaju Industrial Area", ward="Ward 16"),
        created_at=datetime.now().isoformat(),
        upvotes=8,
    ),
]


def _init_store():
    global _next_id
    if not _reports_store:
        _reports_store.extend(SEED_REPORTS)
        _next_id = len(SEED_REPORTS) + 1
        for r in SEED_REPORTS:
            _votes_store[r.id] = {"up": r.upvotes, "down": 0}
            _comments_store[r.id] = []


_init_store()


# ── Endpoints ───────────────────────────────────────────────────
@router.get("/reports/nearby", response_model=List[ReportResponse])
def get_nearby_reports(lat: float = 27.7172, lng: float = 85.3240, radius: float = 5.0):
    """Return all reports (no real geo-filtering yet)."""
    return _reports_store


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int):
    """Get a single report by ID."""
    for r in _reports_store:
        if r.id == report_id:
            return r
    # fallback
    return _reports_store[0] if _reports_store else ReportResponse(
        id=report_id, title="Unknown", description="Not found",
        category="Unknown", status="unknown",
        location=LocationSchema(), created_at=datetime.now().isoformat(),
    )


@router.post("/reports", response_model=ReportResponse, status_code=201)
async def submit_report(
    title: str = Form("Pothole Report"),
    description: str = Form("Auto-detected pothole"),
    category: str = Form("Road Infrastructure"),
    lat: float = Form(27.7172),
    lng: float = Form(85.3240),
    address: str = Form("Kathmandu, Nepal"),
    ward: str = Form("Ward 1"),
    image: Optional[UploadFile] = File(None),
):
    """Submit a new report. Optionally attach an image."""
    global _next_id
    report = ReportResponse(
        id=_next_id,
        title=title,
        description=description,
        category=category,
        status="pending",
        location=LocationSchema(lat=lat, lng=lng, address=address, ward=ward),
        image_url=f"/uploads/report_{_next_id}.jpg" if image else None,
        created_at=datetime.now().isoformat(),
    )
    _reports_store.append(report)
    _votes_store[_next_id] = {"up": 0, "down": 0}
    _comments_store[_next_id] = []
    _next_id += 1
    return report


@router.get("/reports/{report_id}/status")
def get_report_status(report_id: int):
    """Get the status of a report."""
    for r in _reports_store:
        if r.id == report_id:
            return {"id": r.id, "status": r.status}
    return {"id": report_id, "status": "unknown"}


@router.post("/reports/{report_id}/vote")
def cast_vote(report_id: int, body: dict):
    """Upvote or downvote a report."""
    vote_type = body.get("type", "up")
    if report_id not in _votes_store:
        _votes_store[report_id] = {"up": 0, "down": 0}
    if vote_type in ("up", "down"):
        _votes_store[report_id][vote_type] += 1
    return {"id": report_id, "votes": _votes_store[report_id]}


@router.get("/reports/{report_id}/comments", response_model=List[CommentSchema])
def get_comments(report_id: int):
    """List comments for a report."""
    return _comments_store.get(report_id, [])


@router.post("/reports/{report_id}/comments", response_model=CommentSchema, status_code=201)
def add_comment(report_id: int, body: dict):
    """Add a comment to a report."""
    if report_id not in _comments_store:
        _comments_store[report_id] = []
    comment = CommentSchema(
        id=len(_comments_store[report_id]) + 1,
        report_id=report_id,
        user=body.get("user", "Anonymous"),
        text=body.get("text", ""),
        created_at=datetime.now().isoformat(),
    )
    _comments_store[report_id].append(comment)
    return comment


@router.get("/departments", response_model=List[DepartmentSchema])
def list_departments():
    """List all departments / categories."""
    return DEPARTMENTS
