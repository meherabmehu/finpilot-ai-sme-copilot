"""Use the provider's direct database connection for schema migrations."""

import os
import subprocess
import sys

for key in ("DATABASE_URL_UNPOOLED", "POSTGRES_URL_NON_POOLING"):
    if os.getenv(key):
        os.environ["DATABASE_URL"] = os.environ[key]
        break
subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
if os.getenv("FINPILOT_INITIAL_EMAIL") or os.getenv("FINPILOT_INITIAL_PASSWORD"):
    subprocess.run([sys.executable, "manage.py", "provision_owner"], check=True)
