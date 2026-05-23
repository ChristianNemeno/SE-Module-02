import os

# Set minimum required env vars before any app import so pydantic-settings
# doesn't raise on missing API_KEY in test environments.
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
