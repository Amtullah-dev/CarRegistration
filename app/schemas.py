from flask_marshmallow import Marshmallow
from marshmallow import fields, validate

ma = Marshmallow()

class UserSchema(ma.Schema):
    username = fields.String(required=True, validate=validate.Length(min=3))
    password = fields.String(required=True, validate=validate.Length(min=6))

class CarSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    make = fields.String()
    model = fields.String()
    year = fields.Integer()
