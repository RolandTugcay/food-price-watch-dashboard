# connection.py
import os
import psycopg

from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL

load_dotenv()

required_variables = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
missing_variables = [
    name for name in required_variables if not os.getenv(name)
]

if missing_variables:
    raise RuntimeError(
        "Missing database environment variables: "
        + ", ".join(missing_variables)
    )

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.environ["DB_NAME"],
    query={"sslmode": "require"},
)

db = SQLAlchemy()