from repositories import contacts_repository
from utils.text import get_page_offset, parse_bool


def get_recent_contact_requests():
    return contacts_repository.list_recent_contacts()


def get_paginated_contacts(q="", page=1, per_page=8):
    keyword = f"%{q.strip()}%"
    return contacts_repository.list_paginated_contacts(keyword, per_page, get_page_offset(page, per_page))


def get_contact_record(contact_id):
    return contacts_repository.get_contact_record(contact_id)


def normalize_contact_payload(payload):
    name = str(payload.get("name", "")).strip()
    company = str(payload.get("company", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    email = str(payload.get("email", "")).strip()
    contact = str(payload.get("contact", "")).strip() or email or phone
    country = str(payload.get("country", "")).strip()
    interested_product = str(payload.get("interested_product", "")).strip()
    attachment_url = str(payload.get("attachment_url", "")).strip()
    message = str(payload.get("message", "")).strip()
    status = str(payload.get("status", "new")).strip() or "new"

    if not name or not contact:
        raise ValueError("Họ tên và thông tin liên hệ là bắt buộc.")
    captcha_answer = str(payload.get("captcha_answer", "")).strip()
    if captcha_answer and captcha_answer != "7":
        raise ValueError("Captcha liên hệ không đúng.")

    return {
        "name": name,
        "contact": contact,
        "company": company,
        "phone": phone,
        "email": email,
        "country": country,
        "interested_product": interested_product,
        "attachment_url": attachment_url,
        "message": message,
        "status": status,
        "is_read": parse_bool(payload.get("is_read")),
        "note": str(payload.get("note", "")).strip(),
    }


def save_contact(payload, contact_id=None):
    contact = normalize_contact_payload(payload)
    if contact_id:
        contacts_repository.update_contact_record(contact_id, contact)
        return get_contact_record(contact_id)
    new_id = contacts_repository.insert_contact(contact)
    return get_contact_record(new_id)


def delete_contact(contact_id):
    item = get_contact_record(contact_id)
    if not item:
        return None
    contacts_repository.delete_contact_record(contact_id)
    return item


def get_contacts_csv_rows():
    return contacts_repository.list_all_contacts()
