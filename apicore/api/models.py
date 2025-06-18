from django.db import models
from django.conf import settings

# Create your models here.
class Post(models.Model):
    link = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    creator = models.TextField(blank=True)
    pub_date = models.DateTimeField(auto_now=True)
    content = models.TextField(blank=True)
    cat = models.ForeignKey('Category', on_delete=models.PROTECT, null=True)

    def __str__(self):
        return self.title

class Category(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class Staff(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    title = models.CharField(max_length=255)
    position = models.CharField(max_length=255, blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    bg_color = models.CharField(max_length=9, default="#FFFFFF")
    fg_color = models.CharField(max_length=9, default="#000000")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


