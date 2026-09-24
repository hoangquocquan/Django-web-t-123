"""Common read-only model helpers for legacy database mappings."""

from django.db import models


class ReadOnlyQuerySet(models.QuerySet):
    """QuerySet that blocks bulk write operations against legacy tables."""

    def update(self, **kwargs):
        """Block bulk updates for legacy read-only models."""
        raise RuntimeError("Legacy ORM models are read-only; bulk update is disabled.")

    def delete(self):
        """Block bulk deletes for legacy read-only models."""
        raise RuntimeError("Legacy ORM models are read-only; bulk delete is disabled.")


class LegacyReadOnlyManager(models.Manager.from_queryset(ReadOnlyQuerySet)):
    """Manager that exposes the read-only queryset by default."""


class LegacyReadOnlyModel(models.Model):
    """Base class for unmanaged legacy models that must never be written by Django."""

    objects = LegacyReadOnlyManager()

    class Meta:
        abstract = True
        managed = False

    def save(self, *args, **kwargs):
        """Block accidental instance writes to legacy tables."""
        raise RuntimeError("Legacy ORM models are read-only; save is disabled.")

    def delete(self, *args, **kwargs):
        """Block accidental instance deletes from legacy tables."""
        raise RuntimeError("Legacy ORM models are read-only; delete is disabled.")
