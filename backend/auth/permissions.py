def has_admin_permission(admin_user, module_name, action="read"):
    """Phân quyền CMS đơn giản theo role admin/editor/viewer."""
    role = admin_user.get("role")
    if role == "admin":
        return True
    if role == "editor":
        return module_name in {
            "dashboard",
            "products",
            "categories",
            "news",
            "media",
            "pages",
            "menus",
            "banners",
            "contacts",
            "quotes",
            "customers",
            "newsletter",
            "ai",
            "developer",
        } and action in {"read", "write"}
    if role == "viewer":
        return action == "read"
    return False
