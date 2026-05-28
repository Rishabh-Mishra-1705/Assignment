import uuid
from django.db import models


class Organization(models.Model):
    """
    Multi-tenancy root. Every record belongs to an organization.
    In a real system, this would link to user authentication.
    For this prototype we ship one default org seeded in migrations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']