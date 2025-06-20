from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from app.models import Job, User, Application
from app.schemas import JobSchema
from app import db
from app.utils import base_response, paginated_response, role_required
from flasgger import swag_from

bp = Blueprint('jobs', __name__, url_prefix='/jobs')

job_schema = JobSchema()

@bp.route('', methods=['POST'])
@jwt_required()
@role_required('company')
@swag_from({'tags': ['Jobs'], 'summary': 'Create job', 'description': 'Create a new job (company only).', 'parameters': [{'name': 'body', 'in': 'body', 'required': True, 'schema': {'type': 'object', 'properties': {'title': {'type': 'string'}, 'description': {'type': 'string'}, 'location': {'type': 'string'}}, 'required': ['title', 'description']}}], 'responses': {201: {'description': 'Job created'}, 400: {'description': 'Validation failed'}}})
def create_job():
    data = request.get_json()
    errors = job_schema.validate(data)
    if errors:
        return base_response(False, 'Validation failed', None, list(errors.values())), 400
    identity = get_jwt_identity()
    job = Job(
        title=data['title'],
        description=data['description'],
        location=data.get('location'),
        created_by=identity['id']
    )
    db.session.add(job)
    db.session.commit()
    return base_response(True, 'Job created', job_schema.dump(job)), 201

@bp.route('/<uuid:job_id>', methods=['PUT'])
@jwt_required()
@role_required('company')
@swag_from({'tags': ['Jobs'], 'summary': 'Update job', 'description': 'Update a job (company only, own jobs).', 'parameters': [{'name': 'job_id', 'in': 'path', 'type': 'string', 'required': True}], 'responses': {200: {'description': 'Job updated'}, 400: {'description': 'Validation failed'}, 403: {'description': 'Unauthorized access'}, 404: {'description': 'Job not found'}}})
def update_job(job_id):
    identity = get_jwt_identity()
    job = Job.query.get(job_id)
    if not job:
        return base_response(False, 'Job not found', None, ['Job not found']), 404
    if str(job.created_by) != identity['id']:
        return base_response(False, 'Unauthorized access', None, ['Unauthorized access']), 403
    data = request.get_json()
    errors = job_schema.validate(data, partial=True)
    if errors:
        return base_response(False, 'Validation failed', None, list(errors.values())), 400
    if 'title' in data:
        job.title = data['title']
    if 'description' in data:
        job.description = data['description']
    if 'location' in data:
        job.location = data['location']
    db.session.commit()
    return base_response(True, 'Job updated', job_schema.dump(job)), 200

@bp.route('/<uuid:job_id>', methods=['DELETE'])
@jwt_required()
@role_required('company')
@swag_from({'tags': ['Jobs'], 'summary': 'Delete job', 'description': 'Delete a job (company only, own jobs).', 'parameters': [{'name': 'job_id', 'in': 'path', 'type': 'string', 'required': True}], 'responses': {200: {'description': 'Job deleted'}, 403: {'description': 'Unauthorized access'}, 404: {'description': 'Job not found'}}})
def delete_job(job_id):
    identity = get_jwt_identity()
    job = Job.query.get(job_id)
    if not job:
        return base_response(False, 'Job not found', None, ['Job not found']), 404
    if str(job.created_by) != identity['id']:
        return base_response(False, 'Unauthorized access', None, ['Unauthorized access']), 403
    db.session.delete(job)
    db.session.commit()
    return base_response(True, 'Job deleted', None), 200

@bp.route('', methods=['GET'])
@jwt_required()
@role_required('applicant')
@swag_from({'tags': ['Jobs'], 'summary': 'Browse jobs', 'description': 'Browse jobs (applicant only, with filters and pagination).', 'parameters': [{'name': 'title', 'in': 'query', 'type': 'string'}, {'name': 'location', 'in': 'query', 'type': 'string'}, {'name': 'company_name', 'in': 'query', 'type': 'string'}, {'name': 'page', 'in': 'query', 'type': 'integer'}, {'name': 'page_size', 'in': 'query', 'type': 'integer'}], 'responses': {200: {'description': 'Jobs fetched'}}})
def browse_jobs():
    title = request.args.get('title', '').lower()
    location = request.args.get('location', '').lower()
    company_name = request.args.get('company_name', '').lower()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    query = Job.query.join(User, Job.created_by == User.id)
    if title:
        query = query.filter(func.lower(Job.title).contains(title))
    if location:
        query = query.filter(func.lower(Job.location).contains(location))
    if company_name:
        query = query.filter(func.lower(User.name).contains(company_name))
    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    jobs_data = [job_schema.dump(job) for job in jobs]
    return paginated_response(True, 'Jobs fetched', jobs_data, page, page_size, total)

@bp.route('/<uuid:job_id>', methods=['GET'])
@jwt_required()
@swag_from({'tags': ['Jobs'], 'summary': 'Job details', 'description': 'Get job details (all authenticated users).', 'parameters': [{'name': 'job_id', 'in': 'path', 'type': 'string', 'required': True}], 'responses': {200: {'description': 'Job details'}, 404: {'description': 'Job not found'}}})
def job_detail(job_id):
    job = Job.query.get(job_id)
    if not job:
        return base_response(False, 'Job not found', None, ['Job not found']), 404
    user = User.query.get(job.created_by)
    job_data = job_schema.dump(job)
    job_data['created_by'] = user.name if user else str(job.created_by)
    return base_response(True, 'Job details', job_data)

@bp.route('/my', methods=['GET'])
@jwt_required()
@role_required('company')
@swag_from({'tags': ['Jobs'], 'summary': 'View my posted jobs', 'description': 'View my posted jobs (company only, paginated, with application count).', 'parameters': [{'name': 'page', 'in': 'query', 'type': 'integer'}, {'name': 'page_size', 'in': 'query', 'type': 'integer'}], 'responses': {200: {'description': 'My jobs fetched'}}})
def my_jobs():
    identity = get_jwt_identity()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    query = Job.query.filter_by(created_by=identity['id'])
    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    jobs_data = []
    for job in jobs:
        app_count = Application.query.filter_by(job_id=job.id).count()
        job_info = job_schema.dump(job)
        job_info['application_count'] = app_count
        jobs_data.append(job_info)
    return paginated_response(True, 'My jobs fetched', jobs_data, page, page_size, total)
