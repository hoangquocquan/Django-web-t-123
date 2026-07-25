class AppError(Exception):
    """Lỗi chủ động của ứng dụng, có status code và mã lỗi rõ ràng."""

    def __init__(self, message, status=400, code="APP_ERROR"):
        # message là nội dung lỗi cho người dùng/frontend.
        # status là HTTP status code, ví dụ 400, 404, 409.
        # code là mã lỗi ổn định để frontend dễ xử lý bằng code.
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
