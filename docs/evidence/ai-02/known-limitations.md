# AI-02 Known Limitations

- Redis runtime server chưa được xác minh vì môi trường hiện không bật Redis; atomic Lua contract được unit test.
- Rule set cần quy trình cập nhật định kỳ theo threat model thực tế.
- Organization ID chưa có model tenant riêng nên endpoint phải truyền context khi hệ thống đa tenant được bật.
