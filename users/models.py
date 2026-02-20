from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


DEFAULT_AVATAR = (
    'https://res.cloudinary.com/demo/image/upload/'
    'c_fill,w_200,h_200/d_avatar.png/non_existing.png'
)


class User(AbstractUser):
    """
    Custom user: email must be unique.
    Two users cannot share the same password (checked at serializer level
    because hashed passwords are always different at the DB level — the
    business-rule validation lives in RegisterSerializer).
    """
    email = models.EmailField(unique=True)

    REQUIRED_FIELDS = ['email']   # email required alongside username

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    avatar = CloudinaryField(
        'avatar',
        default=DEFAULT_AVATAR,
        blank=True,
        null=True,
    )
    phone = models.CharField(max_length=20, blank=True)
    bio   = models.TextField(blank=True)

    def __str__(self):
        return f'Profile({self.user.username})'
