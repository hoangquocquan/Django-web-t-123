"""Repository nền cho các model catalog đọc từ database legacy."""


class LegacyCatalogRepository:
    """Chuẩn hóa cách repository catalog truy cập database legacy."""

    database_alias = "legacy"
    model = None

    def queryset(self):
        """Tạo QuerySet gốc luôn trỏ tới database alias `legacy`."""
        if self.model is None:
            raise NotImplementedError("Repository con phải khai báo model.")

        return self.model.objects.using(self.database_alias)
