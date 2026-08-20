import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file (important for PythonAnywhere deployment)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crowdfunding_egypt.settings")
application = get_wsgi_application()
