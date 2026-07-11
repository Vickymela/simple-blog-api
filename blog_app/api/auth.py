from ninja import Router
from ..schema import *
from ..models import BlackListedToken,OTP
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from ninja_jwt.tokens import RefreshToken
import jwt
from django.conf import settings
from datetime import datetime,timedelta


User = get_user_model()


auth_api = Router(tags=["auth"])


def create_token(user):
     exp = datetime.now() + timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS)
     payload= {
          'user_id':user.id,
          'exp':exp
     }
     token =jwt.encode(payload,settings.JWT_SECRET,algorithm=settings.JWT_ALGORITHM)
     return token



@auth_api.post("register/",response={201:TokenSchema,400:MessageSchema}, auth=None)
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


@auth_api.post("login/", auth=None)
def login_user(request,user:userloginschema):
    verifed = authenticate(username=user.username,password=user.password)
    if verifed is None:
        raise HttpError(409,"incorrect credentials")
    
    #creates token for the user
   
    token=create_token(verifed)

    return {
        "access_token": token,
        "detail":"login sucessful",
        "username": verifed.username
    }
    

@auth_api.post("logout/")
def logout(request):
    # Get the token from the Authorization header
    token = request.auth  # Django Ninja puts the decoded payload here
    
    # But we need the raw token string — get it from the header
    raw_token = request.headers.get("Authorization").replace("Bearer ", "")
    
    # Save it to the blacklist
    BlackListedToken.objects.get_or_create(token=raw_token)
    
    return {"message": "Logged out successfully"}

####################################################################

@auth_api.put("change_password/",response=MessageSchema)
def change_password(request,current_password:str,new_password:str):
        user= request.auth
        if not user.check_password(current_password):
            return {"message":"this password is incorrect"}
        user.set_password(new_password)
        user.save()
        return {"message":"password changed successfully"}
        

@auth_api.post("forgot_password/", auth=None, response=MessageSchema)
def forgot_password(request, user_email:str):
    user = User.objects.filter(email=user_email).first()
    if not user:
        return 404, {"message": "this user does not exist"}
    
    otp_code= OTP.generate_otp()
    otp = OTP.objects.create(
        user=user,
        code=otp_code
    )
    
    print(f"OTP for {user_email}: {otp.code}")

    return {"message": "OTP sent to your email"} 
    

@auth_api.post("reset_password/", auth=None, response={200:MessageSchema,400:MessageSchema,404:MessageSchema, 429:MessageSchema})
def reset_Password(request, email:str, new_password:str, otp_code:int):
    user = User.objects.filter(email=email).first()
    if not user:
        return 404, {"message":"this user does not exist"}
    
    if not OTP.objects.filter(user=user,code=otp_code).exists():
        return 400, {"message":"Invalid OTP"}
    
    otp_obj = OTP.objects.get(code=otp_code)
    if otp_obj.is_expired():
        return 400, {"meessage":"this otp is expired"}
    
    if OTP.objects.filter(user=user,code=otp_code).exists():
        user = user
        user.set_password(new_password)
        user.save()
    return 200, {"message":"password reset successful"}  
