"""Views Django cho module Accounts/Auth."""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import AdminSession, AdminUser
from .services import (
    change_password,
    login_admin,
    logout_session,
    request_password_reset,
    reset_password_with_token,
    session_to_dict,
    set_account_active,
    user_to_dict,
)


def read_json_body(request):
    """Đọc JSON body thành dict."""
    return json.loads(request.body.decode("utf-8") or "{}")


def accounts_home(request):
    """Trang demo danh sách admin user và session."""
    return render(request, "accounts/accounts_home.html", {"users": AdminUser.objects.all()[:20], "sessions": AdminSession.objects.all()[:20]})


@csrf_exempt
def login_api(request):
    """API đăng nhập admin."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = read_json_body(request)
        session = login_admin(
            payload.get("email", ""),
            payload.get("password", ""),
            request.META.get("REMOTE_ADDR", ""),
            request.META.get("HTTP_USER_AGENT", ""),
            bool(payload.get("remember_login", False)),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"session": session_to_dict(session), "user": user_to_dict(session.admin)})


@csrf_exempt
def logout_api(request):
    """API đăng xuất admin."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    payload = read_json_body(request)
    return JsonResponse({"ok": logout_session(payload.get("session_id", ""))})


def users_api(request):
    """API danh sách admin user."""
    return JsonResponse({"results": [user_to_dict(user) for user in AdminUser.objects.all()]})


def sessions_api(request):
    """API danh sách session admin."""
    return JsonResponse({"results": [session_to_dict(session) for session in AdminSession.objects.all()]})


@csrf_exempt
def forgot_password_api(request):
    """API tạo link reset password demo."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    payload = read_json_body(request)
    reset_link = request_password_reset(payload.get("email", ""), payload.get("base_url", "http://127.0.0.1:8000"))
    return JsonResponse({"message": "Nếu email tồn tại, hệ thống đã tạo link reset.", "reset_link": reset_link})


@csrf_exempt
def reset_password_api(request):
    """API reset password bằng token."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = read_json_body(request)
        admin = reset_password_with_token(payload.get("token", ""), payload.get("password", ""))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"message": "Đã đổi mật khẩu.", "user": user_to_dict(admin)})


@csrf_exempt
def change_password_api(request):
    """API đổi mật khẩu khi đã biết admin_id."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    try:
        payload = read_json_body(request)
        admin = change_password(payload.get("admin_id"), payload.get("current_password", ""), payload.get("new_password", ""))
    except (AdminUser.DoesNotExist, ValueError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"message": "Đã đổi mật khẩu.", "user": user_to_dict(admin)})


@csrf_exempt
def account_status_api(request, admin_id):
    """API khóa hoặc mở khóa tài khoản."""
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST."}, status=405)
    payload = read_json_body(request)
    admin = set_account_active(admin_id, payload.get("is_active", True))
    return JsonResponse({"user": user_to_dict(admin)})
