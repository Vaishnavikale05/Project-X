#!/usr/bin/env python
"""Django management entry point for the Project-X backend skeleton."""

import os
import sys


def main() -> None:
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "project_x_backend.config.settings.development"
    )
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
