from ninja import NinjaAPI
from .schema import *
from .models import Post
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout

User = get_user_model()

main_api = NinjaAPI()

#register users
# login users 
# logout users
# STUDY THIS CODE AND UNDERSTAND HOW IT WORKS AND BE ABLE TO RECREATE OFF HEAD

@main_api.post("register/")
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
    return {"username": new_user.username,
            "email":new_user.email,
            "detail":"registeration sucessful"}

@main_api.post("login/")
def login_user(request,user:userloginschema):
    verifed = authenticate(username=user.username,password=user.password)
    if verifed is None:
        raise HttpError(409,"this is not a user please login")
    auth_login(request,verifed)
    return {"username":user.username,
            "details":"login successful"}

@main_api.post("logout/")
def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        return {"details":"logout sucessful"}
    return {"error":"not a logged in user"}


@main_api.post("postblog/")
def createpost(request,post:PostSchemaInput):
    if request.user.is_authenticated:
        if Post.objects.filter(title=post.title).exists():
            raise HttpError(409,"this post already exits change the name ")
        author = request.user
        new_post = Post.objects.create(
            title = post.title,
            content = post.content,
            author = author
        )
        new_post.save()
        return {"title": new_post.title,
                "content": new_post.content,
                "author": new_post.author.username,
                "details":"post created sucessfully"}
    return {"error":"user is not logged in "}



@main_api.get("read/", response=list[PostSchemaOutput])
def readposts(request):
    if request.user.is_authenticated:
        user = request.user
        posts= Post.objects.filter(author=user)
           
        if posts is None:
            raise HttpError(404,"no posts found")
        return  [
       {"title": p.title,"content": p.content,"author": p.author.username}  # just the name
       for p in posts ] 
    return {"error":"user is not logged in "}   


# update
# delete

@main_api.put("update_post/{old_title}/")
def update_post(request,old_title:str,new_post:UpdateSchema):
    if request.user.is_authenticated:
        post = Post.objects.filter(title=old_title,author=request.user).first()
        if not post:    
            raise HttpError(409,"this title does not exist")
        post.title = new_post.title
        post.content = new_post.content
        post.author = request.user
        post.save()
        return {
                "details":"update sucessful",
                "title":post.title,   
                }

       

@main_api.delete("delete{title}/")
def delete_post(request,title:str):
    if request.user.is_authenticated:
        try:
            post = Post.objects.get(title=title, author=request.user)
            post.delete()
            return {"message": f"Deleted post '{title}' successfully"}
        except Post.DoesNotExist:
            return {"error": "Post not found or you do not have permission"}




