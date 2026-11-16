#!/usr/bin/env python
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent / ".env.local"
        load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)