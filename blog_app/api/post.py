from ninja import Router

from blog_app.urls import AuthBearer
from ..schema import *
from ..models import Post
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
import redis
import json

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
def readposts(request):
    user = request.auth
    r = redis.Redis(host='localhost',port=6379,db=0,decode_responses=True)
    cache_key= f"user_posts_{user.id}"
    cached_post= r.get(cache_key)
    if cached_post:
        return json.loads(cached_post)
    print("Returned from Database")

    posts = Post.objects.filter(author=user).order_by('id')

    if not posts.exists():
        raise HttpError(404,"no posts found")

    # Convert the QuerySet into a list of dictionaries
    posts_data = list(
        posts.values(
            "id",
            "title",
            "content"
        )
    )

    # Store the posts in Redis for 60 seconds
    r.set(
        cache_key,
        json.dumps(posts_data),
        ex=60
    )

    # Return the posts
    return posts_data
   
   

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


@post_api.delete("delete/{id}/",auth=AuthBearer())
def delete_post(request, id:int):
    try:
        post = Post.objects.get(id=id, author=request.auth)
        post.delete()
        return {"message": f"Deleted post '{post.title}' successfully"}
    except Post.DoesNotExist:
        return {"error": "Post not found or you do not have permission"}

@post_api.get("serach/{title}/",response=list[PostSchemaOutput])
def search_post(request,q:str):
    return Post.objects.filter(title__icontains=q)

