from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, SlugField
from django.utils.translation import ugettext_lazy as _

from ..base.util import _generate_slug


class User(AbstractUser):
    # First Name and Last Name do not cover name patterns
    #   around the globe, or among all oauth providers.
    slug = SlugField(max_length=6, unique=True, editable=False, default=_generate_slug,
                     help_text="The external facing identifier for this record")

    name = CharField(_("Name of User"), blank=True, max_length=255)

    # def get_absolute_url(self):
    #     FIXME: Implement a per-user profile page
    #     return reverse("users:detail", kwargs={"username": self.username})

    @property
    def display_name(self):
        """If no name is available, default to the public user ID (slug)"""
        return self.name or self.get_full_name() or self.slug

    def save(self, *args, **kwargs):
        """Generate a slug and ensure it is unique"""
        while True:  # Ensure creation of a random, unique slug
            if self.pk:  # ...but only if the record is new
                break

            slug = _generate_slug()
            if not User.objects.filter(slug=slug).first():
                self.slug = slug
                break

        super().save(*args, **kwargs)
