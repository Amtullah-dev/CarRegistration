from marshmallow import fields, Schema


class CarSchema(Schema):
    id = fields.Integer(dump_only=True)
    make = fields.String(required=True)
    model = fields.String(required=True)
    year = fields.Integer(required=True)
    