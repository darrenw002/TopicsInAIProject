import os
import openai
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///resources.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    openai.api_key = "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"