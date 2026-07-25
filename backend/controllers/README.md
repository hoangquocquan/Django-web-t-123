# Controllers

Controller là lớp nhận yêu cầu từ route rồi gọi service để xử lý nghiệp vụ.

Luồng chuẩn:

```text
app.py route
→ controllers
→ services
→ repositories
→ database
```

File hiện có:

- `api_controller.py`: controller cho các API quan trọng như sản phẩm, liên hệ, OpenAPI.

Khi thêm API mới, nên tạo hàm controller trước, sau đó để `app.py` gọi hàm đó. Như vậy `app.py` không bị phình quá lớn.

Controller chỉ nên nhận request, gọi service, rồi trả response. Không viết SQL trực tiếp ở đây.
