from repositories import public_repository


def get_home_data():
    """Gom dữ liệu cần thiết cho trang chủ."""
    return {
        "products": public_repository.list_featured_product_overview(),
        "capabilities": public_repository.list_capabilities(),
        "news": public_repository.list_news(limit=3),
    }


def get_capabilities():
    """Trả về danh sách năng lực sản xuất."""
    return public_repository.list_capabilities()


def get_news(limit=None):
    """Trả về danh sách tin tức; có thể giới hạn số lượng bằng limit."""
    return public_repository.list_news(limit=limit)
