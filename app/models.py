import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from . import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('applicant', 'company', name='user_roles'), nullable=False)
    jobs = db.relationship('Job', backref='company', lazy=True)
    applications = db.relationship('Application', backref='applicant', lazy=True)

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    location = db.Column(db.String(255))
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='job', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.id'), nullable=False)
    resume_link = db.Column(db.String(255), nullable=False)
    cover_letter = db.Column(db.String(200))
    status = db.Column(db.Enum('Applied', 'Reviewed', 'Interview', 'Rejected', 'Hired', name='application_status'), default='Applied')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('applicant_id', 'job_id', name='unique_application'),) 