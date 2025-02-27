import os
import openai
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///resources.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    openai.api_key = "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"