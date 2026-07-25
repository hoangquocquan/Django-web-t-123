import logging

from config.settings import LOG_ROOT


def setup_logging():
    """Cấu hình logging ra file để dễ truy vết lỗi khi chạy thực tế."""
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_ROOT / "app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

