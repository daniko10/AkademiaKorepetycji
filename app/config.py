import os
from dotenv import load_dotenv

load_dotenv()


class TestConfig():
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'