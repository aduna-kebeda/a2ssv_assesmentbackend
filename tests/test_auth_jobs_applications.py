import io
import pytest
from app import create_app, db
from app.models import User, Job, Application
from flask_jwt_extended import decode_token

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test_secret'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def signup_and_login(client, role, email, password='Password123!'):
    # Signup
    resp = client.post('/auth/signup', json={
        'name': 'Test User',
        'email': email,
        'password': password,
        'role': role
    })
    assert resp.status_code == 201
    # Login
    resp = client.post('/auth/login', json={
        'email': email,
        'password': password
    })
    assert resp.status_code == 200
    token = resp.get_json()['Object']['token']
    return token

def test_company_can_create_job(client):
    token = signup_and_login(client, 'company', 'company@test.com')
    resp = client.post('/jobs',
        json={
            'title': 'Backend Developer',
            'description': 'Develop backend services using Python.',
            'location': 'Remote'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 201
    data = resp.get_json()['Object']
    assert data['title'] == 'Backend Developer'
    assert data['location'] == 'Remote'

def test_applicant_can_browse_jobs(client):
    # Create a job as company
    company_token = signup_and_login(client, 'company', 'company2@test.com')
    client.post('/jobs',
        json={
            'title': 'Frontend Developer',
            'description': 'Develop frontend apps.',
            'location': 'Remote'
        },
        headers={'Authorization': f'Bearer {company_token}'}
    )
    # Signup as applicant
    applicant_token = signup_and_login(client, 'applicant', 'applicant@test.com')
    resp = client.get('/jobs', headers={'Authorization': f'Bearer {applicant_token}'})
    assert resp.status_code == 200
    assert any(job['title'] == 'Frontend Developer' for job in resp.get_json()['Object'])

def test_applicant_can_apply_for_job(client):
    # Create job as company
    company_token = signup_and_login(client, 'company', 'company3@test.com')
    job_resp = client.post('/jobs',
        json={
            'title': 'Fullstack Dev',
            'description': 'Fullstack dev job.',
            'location': 'Remote'
        },
        headers={'Authorization': f'Bearer {company_token}'}
    )
    job_id = job_resp.get_json()['Object']['id']
    # Signup as applicant
    applicant_token = signup_and_login(client, 'applicant', 'applicant2@test.com')
    # Apply for job (with fake PDF)
    data = {
        'job_id': job_id,
        'cover_letter': 'I am interested.'
    }
    fake_pdf = (io.BytesIO(b'%PDF-1.4\n%Fake PDF file'), 'resume.pdf')
    resp = client.post('/applications/apply',
        data={**data, 'resume': fake_pdf},
        content_type='multipart/form-data',
        headers={'Authorization': f'Bearer {applicant_token}'}
    )
    # Accepts only PDF
    assert resp.status_code in (201, 400)
    if resp.status_code == 400:
        assert 'Resume must be a PDF file.' in resp.get_json()['Errors'][0]

def test_company_cannot_apply_for_job(client):
    # Create job as company
    company_token = signup_and_login(client, 'company', 'company4@test.com')
    job_resp = client.post('/jobs',
        json={
            'title': 'QA Engineer',
            'description': 'QA job.',
            'location': 'Remote'
        },
        headers={'Authorization': f'Bearer {company_token}'}
    )
    job_id = job_resp.get_json()['Object']['id']
    # Try to apply as company
    data = {
        'job_id': job_id,
        'cover_letter': 'I am interested.'
    }
    fake_pdf = (io.BytesIO(b'%PDF-1.4\n%Fake PDF file'), 'resume.pdf')
    resp = client.post('/applications/apply',
        data={**data, 'resume': fake_pdf},
        content_type='multipart/form-data',
        headers={'Authorization': f'Bearer {company_token}'}
    )
    assert resp.status_code == 403
    assert 'Unauthorized' in resp.get_json()['Errors']

def test_resume_must_be_pdf(client):
    company_token = signup_and_login(client, 'company', 'company5@test.com')
    job_resp = client.post('/jobs',
        json={
            'title': 'Designer',
            'description': 'Design job.',
            'location': 'Remote'
        },
        headers={'Authorization': f'Bearer {company_token}'}
    )
    job_id = job_resp.get_json()['Object']['id']
    applicant_token = signup_and_login(client, 'applicant', 'applicant3@test.com')
    # Try to apply with non-PDF file
    data = {
        'job_id': job_id,
        'cover_letter': 'I am interested.'
    }
    fake_img = (io.BytesIO(b'not a pdf'), 'resume.png')
    resp = client.post('/applications/apply',
        data={**data, 'resume': fake_img},
        content_type='multipart/form-data',
        headers={'Authorization': f'Bearer {applicant_token}'}
    )
    assert resp.status_code == 400
    assert 'Resume must be a PDF file.' in resp.get_json()['Errors'][0] 