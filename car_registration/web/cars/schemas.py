from flask_marshmallow import Marshmallow
from marshmallow import fields, validate

ma = Marshmallow()

class CarSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    make = fields.String()
    model = fields.String()
    year = fields.Integer()
    