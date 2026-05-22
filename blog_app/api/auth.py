from ninja import Router
from ..schema import *
from ..models import BlackListedToken
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from ninja_jwt.tokens import RefreshToken
import jwt
from django.conf import settings
from datetime import datetime, timedelta


User = get_user_model()

main_api = Router(tags=["Authentication"])


@main_api.post("register/",response={201:TokenSchema, 400:MessageSchema}, auth=None)
def register_users(request,user:userinputschema):
    if User.objects.filter(email=user.email).exists():
        raise HttpError(409,"this user already exists")
    
    #django default user makes username unique
    if User.objects.filter(username=user.username).exists():
        raise HttpError(409,"this user already exists")
    
    new_user = User.objects.create_user(
        username = user.username,
        email=user.email,
        #this is correct but create user already hashes password
        # password=make_password(user.password)
        password=user.password
    )
    token=create_token(new_user)
    return 201,{"username": new_user.username,
            "id": new_user.id,
            "email":new_user.email,
            "access_token":token,
            "detail":"registeration sucessful"}

def create_token(user):
     exp = datetime.now() + timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS)
     payload= {
          'user_id':user.id,
          'exp':exp
     }
     token =jwt.encode(payload,settings.JWT_SECRET,algorithm=settings.JWT_ALGORITHM)
     return token


@main_api.post("login/", auth=None)
def login_user(request,user:userloginschema):
    verifed = authenticate(username=user.username,password=user.password)
    if verifed is None:
        raise HttpError(409,"this is not a user please login")
    
    #creates token for the user
    refresh = RefreshToken.for_user(verifed)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "detail":"login sucessful",
        "username": verifed.username
    }


@main_api.post("logout/")
def logout(request):
    # Get the token from the Authorization header
    token = request.auth  # Django Ninja puts the decoded payload here
    
    # But we need the raw token string — get it from the header
    raw_token = request.headers.get("Authorization").replace("Bearer ", "")
    
    # Save it to the blacklist
    BlackListedToken.objects.get_or_create(token=raw_token)
    
    return {"message": "Logged out successfully"}
