# Job Listing API

A fully functional RESTful API for job listings, built with Flask, PostgreSQL, JWT authentication, and Cloudinary for file uploads. Includes interactive API documentation with Swagger (Flasgger).

## Features
- User registration and login (company/applicant roles)
- JWT-based authentication and role-based access control
- Companies can post, update, delete, and view jobs
- Applicants can browse jobs, apply with resume upload (PDF), and track applications
- File uploads to Cloudinary
- API documentation with Swagger UI

## Tech Stack
- Python 3.11+
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- PostgreSQL
- Flask-JWT-Extended
- Marshmallow
- Cloudinary
- Flasgger (Swagger UI)

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repo-url>
cd job_listing
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the project root with the following:
```
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
JWT_SECRET_KEY=your_jwt_secret_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 5. Initialize the database
```bash
flask db upgrade
```

### 6. Run the application
```bash
flask run
```
The app will be available at `http://127.0.0.1:5000`.

## API Documentation
Interactive docs available at: `http://127.0.0.1:5000/apidocs/`
- Click the **Authorize** button and enter your JWT as `Bearer <token>` to access protected endpoints.

## Authentication
- Register as a company or applicant via `/auth/signup`.
- Log in via `/auth/login` to receive a JWT token.
- Use the JWT token in the `Authorization` header for all protected endpoints.

## File Uploads
- Applicants must upload resumes as PDF files when applying for jobs.
- Files are stored in Cloudinary.

## Example Requests

### Register (Signup)
```bash
curl -X POST http://127.0.0.1:5000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "email": "hr@acme.com", "password": "Password123!", "role": "company"}'
```

### Login
```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "hr@acme.com", "password": "Password123!"}'
```

### Create Job (Company)
```bash
curl -X POST http://127.0.0.1:5000/jobs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Full-Stack Web Developer", "description": "...", "location": "Remote"}'
```

### Apply for Job (Applicant)
```bash
curl -X POST http://127.0.0.1:5000/applications/apply \
  -H "Authorization: Bearer <token>" \
  -F "job_id=<job_id>" \
  -F "cover_letter=I am interested..." \
  -F "resume=@/path/to/resume.pdf"
```

## Troubleshooting
- Ensure your `.env` variables are correct and the database is running.
- Use only PDF files for resume uploads.
- If Swagger UI does not show the lock icon, restart the server and hard refresh the docs page.
- For database errors, check your connection string and run migrations.

## Contact
For questions or support, contact:
- Your Name (<your@email.com>) 