from ninja import NinjaAPI
from .schema import *
from .models import Post
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
#to create token 

from ninja_jwt.tokens import RefreshToken, AccessToken
# to read token from header
from ninja.security import HttpBearer,django_auth
import jwt
from django.conf import settings
from datetime import datetime,timedelta

User = get_user_model()




class AuthBearer(HttpBearer):
    #tellin django every request must include a token
    #means the string is sent to the header
    def authenticate(self, request, token):
        print("TOKEN RECEIVED:", token[:30])

        try:
            payload = jwt.decode(token,settings.JWT_SECRET,algorithms=[settings.JWT_ALGORITHM])
            user= User.objects.get(id=payload['user_id'])
            return user
        except jwt.ExpiredSignatureError:
            return None
        except(jwt.InvalidTokenError,User.DoesNotExist):
            return None


        #     # CHATGPT|
        #     #checks if token is valid and not expired
        #     decoded = AccessToken(token)
        #     decoded.verify()
        #     print("TOKEN PAYLOAD:", decoded.payload)
        #     #extracts user id stored in the token 
        #     # token contains type,payload and signaature
        #     #payload has the userid,eexpiration,created at,and custom data
        #     user_id = decoded.payload.get("user_id")
        #     print("USER ID:", user_id) 
        #     user = User.objects.get(id=user_id)
        #     return user
        # #this becomes request.auth
        # except Exception as e:
        #     print("AUTH ERROR:" , str(e)) 
        #     raise HttpError(401, "Invalid or expired token")
        
        

   
main_api = NinjaAPI(auth=[django_auth,AuthBearer()])
#register users
# login users 
# logout users
# STUDY THIS CODE AND UNDERSTAND HOW IT WORKS AND BE ABLE TO RECREATE OFF HEAD

@main_api.post("register/",response={201:TokenSchema,400:MessageSchema})
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
    token=create_token(user)
    return 201,{"username": new_user.username,
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


@main_api.post("login/")
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
    

    # auth_login(request,verifed)
    # return {"username":user.username,
    #         "details":"login successful"}
# @main_api.post("logout/")
# def logout_user(request):
#     if request.user.is_authenticated:
#         logout(request)
#         return {"details":"logout sucessful"}
#     return {"error":"not a logged in user"}


@main_api.post("postblog/",auth=AuthBearer())
def createpost(request,post:PostSchemaInput):
    if Post.objects.filter(title=post.title).exists():
        raise HttpError(409,"this post already exits change the name ")
    author = request.auth
    new_post = Post.objects.create(
        title = post.title,
        content = post.content,
        author = author
    )
    # new_post.save()
    return {"title": new_post.title,
            "content": new_post.content,
            "author": new_post.author.username,
            "details":"post created sucessfully"}




@main_api.get("read/",auth=AuthBearer(),response=list[PostSchemaOutput])
def readposts(request):

        user = request.auth
        posts= Post.objects.filter(author=user)
           
        if not posts.exists():
            raise HttpError(404,"no posts found")
        return  [
       {"title": p.title,"content": p.content,"author": p.author.username}  # just the name
       for p in posts ] 
   


# update
# delete

@main_api.put("update_post/{old_title}/",auth=AuthBearer())
def update_post(request,old_title:str,new_post:UpdateSchema):
    
        post = Post.objects.filter(title=old_title,author=request.auth).first()
        if not post:    
            raise HttpError(409,"this title does not exist")
        post.title = new_post.title
        post.content = new_post.content
        post.author = request.auth
        post.save()
        return {
                "details":"update sucessful",
                "title":post.title,   
                }

       

@main_api.delete("delete/{title}/",auth=AuthBearer())
def delete_post(request,title:str):
   
        try:
            post = Post.objects.get(title=title, author=request.auth)
            post.delete()
            return {"message": f"Deleted post '{title}' successfully"}
        except Post.DoesNotExist:
            return {"error": "Post not found or you do not have permission"}




