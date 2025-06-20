from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    role = fields.Str(validate=validate.OneOf(["company", "applicant"]))

class JobSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=True, validate=validate.Length(min=20, max=2000))
    location = fields.Str()
    created_by = fields.UUID()
    created_at = fields.DateTime()

class ApplicationSchema(Schema):
    id = fields.UUID(dump_only=True)
    applicant_id = fields.UUID()
    job_id = fields.UUID()
    resume_link = fields.Url(required=True)
    cover_letter = fields.Str(validate=validate.Length(max=200))
    status = fields.Str(validate=validate.OneOf(["Applied", "Reviewed", "Interview", "Rejected", "Hired"]))
    applied_at = fields.DateTime() 