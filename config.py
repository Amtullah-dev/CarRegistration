import os


class Config:
    # Basic Flask settings
    SECRET_KEY = 'your-secret-key'

    # Database
    # New MySQL DB 
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:aj-dev014%400126@localhost/test1'
    # Testing
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:aj-dev014%400126@localhost/test'
    # for Docker
    # Populated DB
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:aj-dev014%400126@host.docker.internal/test1'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:aj-dev014%400126@host.docker.internal/test2'

    DB_USER = os.getenv("DB_USER", "myuser")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "mypass")
    DB_NAME = os.getenv("DB_NAME", "mydb")
    DB_HOST = os.getenv("DB_HOST", "db")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_SECRET_KEY = 'your-jwt-secret'

    GRPC_SERVER_ADDRESS ='grpc-server:50051'

    # Parse settings
    PARSE_APP_ID = 'hlhoNKjOvEhqzcVAJ1lxjicJLZNVv36GdbboZj3Z'
    PARSE_API_KEY = 'SNMJJF0CZZhTPhLDIqGhTlUNV9r60M2Z5spyWfXW'
