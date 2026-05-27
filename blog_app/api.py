from ninja import NinjaAPI, Swagger
from .schema import *
from .models import Post,BlackListedToken,OTP
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from ninja_jwt.tokens import RefreshToken, AccessToken
from ninja.security import HttpBearer,django_auth
import jwt
from django.conf import settings
from datetime import datetime,timedelta
from ninja.pagination import paginate, PageNumberPagination
import secrets
from django.utils import timezone


User = get_user_model()


class AuthBearer(HttpBearer):
    #tellin django every request must include a token
    #means the string is sent to the header
    def authenticate(self, request, token):
        print("TOKEN RECEIVED:", token[:30])

        # 1. Check if this token is blacklisted
        if BlackListedToken.objects.filter(token=token).exists():
            return None  # reject it


        try:
            payload = jwt.decode(token,settings.JWT_SECRET,algorithms=[settings.JWT_ALGORITHM])

            user = User.objects.get(id=payload['user_id'])
            return user
        except jwt.ExpiredSignatureError:
            return None
        except(jwt.InvalidTokenError,User.DoesNotExist):
            return None

        

main_api = NinjaAPI(auth=[AuthBearer()], docs=Swagger(settings={"persistAuthorization": True}))



def create_token(user):
     exp = datetime.now() + timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS)
     payload= {
          'user_id':user.id,
          'exp':exp
     }
     token =jwt.encode(payload,settings.JWT_SECRET,algorithm=settings.JWT_ALGORITHM)
     return token



@main_api.post("register/",response={201:TokenSchema,400:MessageSchema}, auth=None)
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


@main_api.post("login/", auth=None)
def login_user(request,user:userloginschema):
    verifed = authenticate(username=user.username,password=user.password)
    if verifed is None:
        raise HttpError(409,"incorrect credentials")
    
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

####################################################################

@main_api.put("change_password/",response=MessageSchema)
def change_password(request,current_password:str,new_password:str):
        user= request.auth
        if not user.check_password(current_password):
            return {"message":"this password is incorrect"}
        user.set_password(new_password)
        user.save()
        return {"message":"password changed successfully"}
        

      
@main_api.get("forgot_password/")
def forgot_password(request,user_email:str):
    if not User.objects.filter(email=user_email).first():
        return {"message": "this user does not exist"}
    otp_code= OTP.generate_otp()
    user = request.auth
    otp = OTP.objects.create(
        user=user,
        code=otp_code
    )
    
    print(f"OTP for {user_email}: {otp.code}")

  
    return {"message": "OTP sent to your email"} 
    

@main_api.get("Reset_password/")
def Reset_Password(request,email:str,new_password:str,otp_code:int):
      if not OTP.objects.filter(user=request.auth,code=otp_code).exists():
          return {"message":"Invalid OTP"}
      otp_obj = OTP.objects.get(code=otp_code)
      if otp_obj.is_expired():
        return {"meessage":"this otp is expired"}
      if OTP.objects.filter(user=request.auth,code=otp_code).exists():
        user = request.auth
        user.set_password(new_password)
        user.save()
        return {"message":"password reset successful"}  

        

    
#####################################################################

@main_api.post("postblog/",auth=AuthBearer(), response=PostSchemaOutput)
def createpost(request,post:PostSchemaInput):
    if Post.objects.filter(title=post.title).exists():
        raise HttpError(409,"this post already exits change the name ")
    
    author = request.auth
    new_post = Post.objects.create(
        title = post.title,
        content = post.content,
        author = author
    )
    return new_post


@main_api.get("read/", auth=AuthBearer(), response=list[PostSchemaOutput])
@paginate(PageNumberPagination, page_size=3)
def readposts(request):
    user = request.auth
    posts = Post.objects.filter(author=user).order_by('id')
   
    
        
    if not posts.exists():
        raise HttpError(404,"no posts found")
    return posts
   

# update
@main_api.put("update_post/{id}/", response=PostSchemaOutput)
def update_post(request, id:int,new_post:UpdateSchema):
    post = Post.objects.filter(id=id,author=request.auth).first()
    if not post:    
        raise HttpError(409,"this post does not exist")
    post.title = new_post.title
    post.content = new_post.content
    post.author = request.auth
    post.save()
    return post


# delete
@main_api.delete("delete/{id}/",auth=AuthBearer())
def delete_post(request, id:int):
    try:
        post = Post.objects.get(id=id, author=request.auth)
        post.delete()
        return {"message": f"Deleted post '{post.title}' successfully"}
    except Post.DoesNotExist:
        return {"error": "Post not found or you do not have permission"}

