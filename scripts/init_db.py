import os
import sys

# Add the 'src' directory to the Python path so it can import 'app'
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from app.core import Base, engine

# Import all models here so SQLAlchemy registers them before create_all
from app.models import PersonalInfo, Project


def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()
