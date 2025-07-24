from functools import wraps
from flask import request, jsonify
from marshmallow import Schema, fields, ValidationError


def validate_json(schema_class):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400

            try:
                schema = schema_class()
                validated_data = schema.load(data)
                return f(validated_data, *args, **kwargs)
            except ValidationError as err:
                return jsonify({"errors": err.messages}), 400

        return decorated_function

    return decorator
