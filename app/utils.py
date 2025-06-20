from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from functools import wraps

def base_response(success, message, obj=None, errors=None):
    return jsonify({
        'Success': success,
        'Message': message,
        'Object': obj,
        'Errors': errors or None
    })

def paginated_response(success, message, obj, page_number, page_size, total_size, errors=None):
    return jsonify({
        'Success': success,
        'Message': message,
        'Object': obj,
        'PageNumber': page_number,
        'PageSize': page_size,
        'TotalSize': total_size,
        'Errors': errors or None
    })

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims or claims.get('role') != role:
                return base_response(False, 'Unauthorized', None, ['Unauthorized']), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator 