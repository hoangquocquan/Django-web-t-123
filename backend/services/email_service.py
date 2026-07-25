from repositories import auth_repository


def send_email(recipient, subject, body):
    """Email Service local: lưu email vào outbox thay vì gửi SMTP thật."""
    # Khi production có SMTP thật, chỉ cần thay logic trong service này.
    recipient = str(recipient or "").strip()
    subject = str(subject or "").strip()
    body = str(body or "").strip()
    if not recipient or "@" not in recipient:
        raise ValueError("Email người nhận không hợp lệ.")
    if not subject:
        raise ValueError("Tiêu đề email là bắt buộc.")
    return auth_repository.create_auth_email(recipient, subject, body)


def send_template_email(recipient, template_name, context):
    """Gửi email theo template đơn giản để code gọi dễ hiểu hơn."""
    subject = f"MecPrecision - {template_name}"
    body_lines = [f"{key}: {value}" for key, value in context.items()]
    return send_email(recipient, subject, "\n".join(body_lines))

