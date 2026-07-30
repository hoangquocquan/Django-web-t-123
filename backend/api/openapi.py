def get_openapi_schema():
    """Tạo tài liệu OpenAPI cho các endpoint quan trọng."""
    # OpenAPI là chuẩn mô tả API. Frontend hoặc đối tác có thể đọc file này
    # để biết endpoint nào tồn tại, gửi dữ liệu gì và nhận dữ liệu gì.
    return {
        # openapi cho biết phiên bản chuẩn OpenAPI đang dùng.
        "openapi": "3.0.3",
        # info là thông tin chung của bộ API.
        "info": {
            "title": "MecPrecision Vietnam API",
            "version": "1.0.0",
            "description": "API local cho website động, CMS và tích hợp bên ngoài.",
        },
        # servers cho biết URL gốc mà client sẽ gọi API.
        "servers": [{"url": "http://127.0.0.1:8000"}],
        # paths là danh sách endpoint. Mỗi endpoint có method GET/POST/PUT/DELETE.
        "paths": {
            "/api/home": {
                "get": {
                    "summary": "Lấy dữ liệu trang chủ",
                    "responses": {"200": {"description": "Dữ liệu trang chủ"}},
                }
            },
            "/api/products": {
                "get": {
                    "summary": "Lấy danh sách sản phẩm",
                    "responses": {"200": {"description": "Danh sách sản phẩm"}},
                },
                "post": {
                    "summary": "Tạo sản phẩm mới",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ProductInput"}
                            }
                        },
                    },
                    "responses": {
                        "201": {"description": "Đã tạo sản phẩm"},
                        "400": {"description": "Dữ liệu không hợp lệ"},
                    },
                },
            },
            "/api/products/{id}": {
                "get": {
                    "summary": "Lấy chi tiết sản phẩm",
                    "parameters": [{"$ref": "#/components/parameters/Id"}],
                    "responses": {"200": {"description": "Chi tiết sản phẩm"}, "404": {"description": "Không tìm thấy"}},
                },
                "put": {
                    "summary": "Cập nhật sản phẩm",
                    "parameters": [{"$ref": "#/components/parameters/Id"}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ProductInput"}
                            }
                        },
                    },
                    "responses": {"200": {"description": "Đã cập nhật"}, "404": {"description": "Không tìm thấy"}},
                },
                "delete": {
                    "summary": "Xóa sản phẩm",
                    "parameters": [{"$ref": "#/components/parameters/Id"}],
                    "responses": {"200": {"description": "Đã xóa"}, "404": {"description": "Không tìm thấy"}},
                },
            },
            "/api/product-categories": {
                "get": {
                    "summary": "Lấy danh mục sản phẩm",
                    "responses": {"200": {"description": "Danh sách danh mục"}},
                }
            },
            "/api/news": {
                "get": {
                    "summary": "Lấy danh sách tin tức",
                    "responses": {"200": {"description": "Danh sách tin tức"}},
                }
            },
            "/api/contact": {
                "post": {
                    "summary": "Gửi yêu cầu liên hệ",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ContactInput"}
                            }
                        },
                    },
                    "responses": {"201": {"description": "Đã lưu liên hệ"}, "400": {"description": "Thiếu dữ liệu"}},
                }
            },
            "/api/quote-request": {
                "post": {
                    "summary": "Gửi yêu cầu báo giá",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QuoteRequestInput"}
                            }
                        },
                    },
                    "responses": {"201": {"description": "Đã tạo yêu cầu báo giá"}, "400": {"description": "Thiếu dữ liệu"}},
                }
            },
            "/api/external/weather": {
                "get": {
                    "summary": "Demo backend gọi API thời tiết bên ngoài",
                    "responses": {"200": {"description": "Dữ liệu thời tiết demo"}},
                }
            },
            "/api/openapi.json": {
                "get": {
                    "summary": "Lấy tài liệu OpenAPI dạng JSON",
                    "responses": {"200": {"description": "OpenAPI schema"}},
                }
            },
            "/api/health": {
                "get": {
                    "summary": "Health Check cho hệ thống",
                    "responses": {"200": {"description": "Trạng thái app/database/cache"}},
                }
            },
            "/api/version": {
                "get": {
                    "summary": "Lấy phiên bản API",
                    "responses": {"200": {"description": "API version"}},
                }
            },
        },
        # components chứa schema dùng lại nhiều lần, ví dụ ProductInput.
        "components": {
            "parameters": {
                "Id": {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                }
            },
            "schemas": {
                # ProductInput mô tả dữ liệu frontend cần gửi khi tạo/sửa sản phẩm.
                "ProductInput": {
                    "type": "object",
                    "required": ["category_id", "name", "short_description", "description", "main_image"],
                    "properties": {
                        "category_id": {"type": "integer", "example": 1},
                        "name": {"type": "string", "example": "Trục truyền động chính xác"},
                        "slug": {"type": "string", "example": "truc-truyen-dong-chinh-xac"},
                        "short_description": {"type": "string"},
                        "description": {"type": "string"},
                        "main_image": {"type": "string"},
                        "is_featured": {"type": "boolean"},
                    },
                },
                # ContactInput mô tả dữ liệu form liên hệ.
                "ContactInput": {
                    "type": "object",
                    "required": ["name", "contact"],
                    "properties": {
                        "name": {"type": "string", "example": "Nguyễn Văn A"},
                        "contact": {"type": "string", "example": "a@example.com"},
                        "message": {"type": "string", "example": "Tôi cần báo giá."},
                    },
                },
                "QuoteRequestInput": {
                    "type": "object",
                    "required": ["name", "product"],
                    "properties": {
                        "name": {"type": "string"},
                        "company": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "product": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "tolerance": {"type": "string"},
                        "drawing_pdf": {"type": "string"},
                        "step_file": {"type": "string"},
                        "dwg_file": {"type": "string"},
                        "deadline": {"type": "string"},
                        "note": {"type": "string"},
                    },
                },
                # ErrorResponse mô tả format lỗi thống nhất của API.
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "VALIDATION_ERROR"},
                                "message": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }
