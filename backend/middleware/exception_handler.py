import sqlite3

from utils.exceptions import AppError


# File này gom xử lý lỗi về một nơi.
# Lợi ích: route/controller/service có lỗi thì frontend vẫn nhận response rõ ràng,
# không bị lỗi 500 mặc định khó hiểu của Python HTTP server.


def handle_request_exception(handler, action, logger, debug=False):
    """Bọc một request bằng exception handler tập trung."""
    # handler là object đang xử lý HTTP request.
    # action là hàm thật sự xử lý GET/POST/PUT/DELETE.
    # Nếu action bị lỗi, hàm này quyết định trả lỗi về frontend như thế nào.
    try:
        action()
    except AppError as error:
        # AppError là lỗi mình chủ động ném ra, ví dụ không tìm thấy sản phẩm.
        handler.send_error_response(error.message, status=error.status, code=error.code)
    except ValueError as error:
        # ValueError thường là lỗi validate dữ liệu form/API.
        handler.send_error_response(str(error), status=400, code="VALIDATION_ERROR")
    except sqlite3.IntegrityError as error:
        # IntegrityError là lỗi ràng buộc database, ví dụ UNIQUE/FOREIGN KEY.
        logger.exception("Database integrity error")
        handler.send_error_response(str(error), status=409, code="DATABASE_CONSTRAINT_ERROR")
    except Exception as error:
        # Đây là lớp bắt lỗi cuối cùng để server không trả lỗi thô khó đọc.
        logger.exception("Unhandled request error")
        message = str(error) if debug else "Có lỗi hệ thống. Vui lòng thử lại sau."
        handler.send_error_response(message, status=500, code="INTERNAL_SERVER_ERROR")
