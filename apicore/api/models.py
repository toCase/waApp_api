from django.db import models

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
