from marshmallow import fields, Schema, validate


class UserSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3))
    password = fields.String(required=True, validate=validate.Length(min=6))

class RegisterSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

class RegisterOutputSchema(Schema):
    message = fields.String(required=True)