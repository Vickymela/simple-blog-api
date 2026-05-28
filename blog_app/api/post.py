from ninja import NinjaAPI, Router, Swagger

from blog_app.urls import AuthBearer
from ..schema import *
from ..models import Post,BlackListedToken,OTP
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

post_api = Router(tags=["posts"])

@post_api.post("postblog/", response=PostSchemaOutput)
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


@post_api.get("read/", response=list[PostSchemaOutput])
@paginate(PageNumberPagination, page_size=3)
def readposts(request):
    user = request.auth

    posts = Post.objects.filter(author=user).order_by('id')

    if not posts.exists():
        raise HttpError(404,"no posts found")
    return posts
   

# update
@post_api.put("update_post/{id}/", response=PostSchemaOutput)
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
@post_api.delete("delete/{id}/",auth=AuthBearer())
def delete_post(request, id:int):
    try:
        post = Post.objects.get(id=id, author=request.auth)
        post.delete()
        return {"message": f"Deleted post '{post.title}' successfully"}
    except Post.DoesNotExist:
        return {"error": "Post not found or you do not have permission"}
