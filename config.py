import os


class Config:
    # Basic Flask settings
    SECRET_KEY = 'your-secret-key'

    # Database
    # New MySQL DB 
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:aj-dev014%400126@localhost/test1'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:aj-dev014%400126@host.docker.internal/test1'

    # JWT settings
    JWT_SECRET_KEY = 'your-jwt-secret'

    # Parse settings
    PARSE_APP_ID = 'hlhoNKjOvEhqzcVAJ1lxjicJLZNVv36GdbboZj3Z'
    PARSE_API_KEY = 'SNMJJF0CZZhTPhLDIqGhTlUNV9r60M2Z5spyWfXW'
