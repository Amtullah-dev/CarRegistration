from marshmallow import fields, Schema, validate


class UserSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3))
    password = fields.String(required=True, validate=validate.Length(min=6))
