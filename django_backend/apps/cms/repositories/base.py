"""Repository base for CMS models stored in the legacy database."""


class LegacyCmsRepository:
    """Standardize CMS repository access through database alias `legacy`."""

    database_alias = "legacy"
    model = None

    def queryset(self):
        """Create a base QuerySet that always reads from the legacy database."""
        if self.model is None:
            raise NotImplementedError("Repository subclass must define model.")

        return self.model.objects.using(self.database_alias)
