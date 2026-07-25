#!/usr/bin/env python
"""Lệnh quản lý Django cho skeleton mới.

Giai đoạn 3 chỉ tạo khung Django, chưa chuyển logic nghiệp vụ từ backend cũ.
Sau này bạn sẽ chạy lệnh kiểu: python mecprecision/manage.py runserver
"""

import os
import sys


def main():
    """Nạp settings Django rồi chuyển lệnh cho Django xử lý."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
