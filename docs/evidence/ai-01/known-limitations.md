# AI-01 Known Limitations

- `DjangoJSONVectorStore` chỉ dành cho local/demo và tìm tuyến tính trong Python.
- PostgreSQL/pgvector chưa được bật vì Docker/PostgreSQL runtime chưa sẵn sàng.
- Production cần reindex toàn bộ bằng model được khóa version trước cutover.
