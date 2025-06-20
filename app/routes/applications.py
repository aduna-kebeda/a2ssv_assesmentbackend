import os
import cloudinary
import cloudinary.uploader
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from app.models import Application, Job, User
from app.schemas import ApplicationSchema
from app import db
from app.utils import base_response, paginated_response, role_required
from werkzeug.utils import secure_filename
from datetime import datetime
from flasgger import swag_from

bp = Blueprint('applications', __name__, url_prefix='/applications')

application_schema = ApplicationSchema()

# Correct Cloudinary config using your provided values
cloudinary.config(
    cloud_name='dpasgcaqm',
    api_key='296661259151749',
    api_secret='O39mS4BgA_5bN2miMuaRI3YTfR0'
)

@bp.route('/apply', methods=['POST'])
@jwt_required()
@role_required('applicant')
@swag_from({'tags': ['Applications'], 'summary': 'Apply for job', 'description': 'Apply for a job (applicant only, with resume upload).', 'consumes': ['multipart/form-data'], 'parameters': [{'name': 'job_id', 'in': 'formData', 'type': 'string', 'required': True}, {'name': 'cover_letter', 'in': 'formData', 'type': 'string'}, {'name': 'resume', 'in': 'formData', 'type': 'file', 'required': True}], 'responses': {201: {'description': 'Application submitted'}, 400: {'description': 'Validation failed'}, 409: {'description': 'Duplicate application'}}})
def apply_job():
    applicant = get_jwt_identity()
    job_id = request.form.get('job_id')
    cover_letter = request.form.get('cover_letter', '')
    resume = request.files.get('resume')
    errors = []
    if not job_id:
        errors.append('Job ID is required.')
    if not resume:
        errors.append('Resume file is required.')
    if cover_letter and len(cover_letter) > 200:
        errors.append('Cover letter must be under 200 characters.')
    if errors:
        return base_response(False, 'Validation failed', None, errors), 400
    job = Job.query.get(job_id)
    if not job:
        return base_response(False, 'Job not found', None, ['Job not found']), 404
    # Check for duplicate application
    existing = Application.query.filter_by(applicant_id=applicant, job_id=job_id).first()
    if existing:
        return base_response(False, 'Duplicate application', None, ['You have already applied to this job.']), 409
    # Upload resume to Cloudinary
    if resume and resume.filename.lower().endswith('.pdf'):
        upload_result = cloudinary.uploader.upload(resume, resource_type='raw', folder='resumes', format='pdf')
        resume_link = upload_result['secure_url']
    else:
        return base_response(False, 'Resume must be a PDF file.', None, ['Resume must be a PDF file.']), 400
    application = Application(
        applicant_id=applicant,
        job_id=job_id,
        resume_link=resume_link,
        cover_letter=cover_letter,
        status='Applied',
        applied_at=datetime.utcnow()
    )
    db.session.add(application)
    db.session.commit()
    return base_response(True, 'Application submitted', application_schema.dump(application)), 201

@bp.route('/my', methods=['GET'])
@jwt_required()
@role_required('applicant')
@swag_from({'tags': ['Applications'], 'summary': 'Track my applications', 'description': 'Track my applications (applicant only, paginated).', 'parameters': [{'name': 'page', 'in': 'query', 'type': 'integer'}, {'name': 'page_size', 'in': 'query', 'type': 'integer'}], 'responses': {200: {'description': 'Applications fetched'}}})
def my_applications():
    identity = get_jwt_identity()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    query = Application.query.filter_by(applicant_id=identity)
    total = query.count()
    applications = query.order_by(Application.applied_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for app in applications:
        job = Job.query.get(app.job_id)
        company = User.query.get(job.created_by) if job else None
        result.append({
            'job_title': job.title if job else None,
            'company_name': company.name if company else None,
            'status': app.status,
            'applied_at': app.applied_at
        })
    return paginated_response(True, 'Applications fetched', result, page, page_size, total)

@bp.route('/job/<uuid:job_id>', methods=['GET'])
@jwt_required()
@role_required('company')
@swag_from({'tags': ['Applications'], 'summary': 'View applications for a job', 'description': 'View applications for a job (company only, own jobs, paginated).', 'parameters': [{'name': 'job_id', 'in': 'path', 'type': 'string', 'required': True}, {'name': 'page', 'in': 'query', 'type': 'integer'}, {'name': 'page_size', 'in': 'query', 'type': 'integer'}], 'responses': {200: {'description': 'Job applications fetched'}, 403: {'description': 'Unauthorized access'}, 404: {'description': 'Job not found'}}})
def job_applications(job_id):
    identity = get_jwt_identity()
    job = Job.query.get(job_id)
    if not job:
        return base_response(False, 'Job not found', None, ['Job not found']), 404
    if str(job.created_by) != identity['id']:
        return base_response(False, 'Unauthorized access', None, ['Unauthorized access']), 403
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    query = Application.query.filter_by(job_id=job_id)
    total = query.count()
    applications = query.order_by(Application.applied_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for app in applications:
        applicant = User.query.get(app.applicant_id)
        result.append({
            'applicant_name': applicant.name if applicant else None,
            'resume_link': app.resume_link,
            'cover_letter': app.cover_letter,
            'status': app.status,
            'applied_at': app.applied_at
        })
    return paginated_response(True, 'Job applications fetched', result, page, page_size, total)

@bp.route('/status/<uuid:application_id>', methods=['PUT'])
@jwt_required()
@role_required('company')
@swag_from({'tags': ['Applications'], 'summary': 'Update application status', 'description': 'Update application status (company only, own jobs).', 'parameters': [{'name': 'application_id', 'in': 'path', 'type': 'string', 'required': True}, {'name': 'body', 'in': 'body', 'required': True, 'schema': {'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['Applied', 'Reviewed', 'Interview', 'Rejected', 'Hired']}}}}], 'responses': {200: {'description': 'Application status updated'}, 400: {'description': 'Invalid status'}, 403: {'description': 'Unauthorized'}, 404: {'description': 'Application not found'}}})
def update_application_status(application_id):
    identity = get_jwt_identity()
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ['Applied', 'Reviewed', 'Interview', 'Rejected', 'Hired']:
        return base_response(False, 'Invalid status', None, ['Invalid status']), 400
    application = Application.query.get(application_id)
    if not application:
        return base_response(False, 'Application not found', None, ['Application not found']), 404
    job = Job.query.get(application.job_id)
    if not job or str(job.created_by) != identity['id']:
        return base_response(False, 'Unauthorized', None, ['Unauthorized']), 403
    application.status = new_status
    db.session.commit()
    return base_response(True, 'Application status updated', application_schema.dump(application)), 200 