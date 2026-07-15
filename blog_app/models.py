from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Post(models.Model):
    title = models.CharField(max_length=350)
    content = models.TextField()
    author = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return self.title
class BlackListedToken(models.Model):
    token = models.CharField(max_length=500)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token

class OTP(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    code = models.IntegerField()
    date_created = models.DateTimeField(auto_now=False, auto_now_add=True)
     
    def __str__(self):
        return self.date_created
    
    @staticmethod
    def generate_otp():
        import secrets
        otp = secrets.randbelow(900000) + 100000
        return otp
    
    def is_expired(self):
         return timezone.now() > self.date_created + timedelta(minutes=5)

