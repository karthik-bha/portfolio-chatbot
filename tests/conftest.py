import os

os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["GEMINI_MODELS"] = '["test-model"]'
os.environ["RATE_LIMIT"] = "1000/minute"