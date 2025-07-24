from marshmallow import fields, Schema, INCLUDE
from apiflask import Schema
from apiflask.fields import Boolean, List, String, DateTime, Nested, Integer

class CarSchema(Schema):
    id = fields.Integer(dump_only=True)
    make = fields.String(required=True)
    model = fields.String(required=True)
    year = fields.Integer(required=True)

class SyncCarsInputSchema(Schema):
    class Meta:
        unknown = INCLUDE

class SyncCarsOutputSchema(Schema):
    message = fields.String(required=True, description="Sync status message")
    result = fields.Raw(required=False, description="Immediate result if sync is direct")
    task_id = fields.String(required=False, description="Celery task ID if async")

class TaskResultOutputSchema(Schema):
    status = fields.String(required=True, description="Task status (e.g., success, pending, failed)")
    cars = fields.List(
        fields.Dict(keys=fields.Str(), values=fields.Raw()),
        required=False,
        description="List of synced cars, if available"
    )
