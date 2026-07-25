"""Repository nền cho các model CRM đọc từ database legacy."""


class LegacyCrmRepository:
    """Chuẩn hóa cách repository CRM truy cập database alias `legacy`."""

    database_alias = "legacy"
    model = None

    def queryset(self):
        """Tạo QuerySet gốc luôn trỏ tới database legacy."""
        if self.model is None:
            raise NotImplementedError("Repository con phải khai báo model.")

        return self.model.objects.using(self.database_alias)
