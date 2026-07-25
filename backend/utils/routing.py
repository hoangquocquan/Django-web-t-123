import re


def parse_product_api_id(path):
    """Lấy id từ URL dạng /api/products/123."""
    match = re.fullmatch(r"/api/products/(\d+)", path)
    return int(match.group(1)) if match else None


def parse_admin_item_path(path, module_name, action):
    """Lấy id từ URL admin dạng /admin/products/12/edit."""
    match = re.fullmatch(rf"/admin/{module_name}/(\d+)/{action}", path)
    return int(match.group(1)) if match else None

