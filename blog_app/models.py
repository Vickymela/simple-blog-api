from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=350)
    content = models.TextField()
    author = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return self.title
