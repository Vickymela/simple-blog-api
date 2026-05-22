from ninja import Router
from ..schema import *
from ..models import Post
from ninja.errors import HttpError
from ninja.pagination import paginate, PageNumberPagination


main_api = Router(tags=["Posts"])


@main_api.post("postblog/", response=PostSchemaOutput)
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


@main_api.get("read/", response=list[PostSchemaOutput])
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
@main_api.delete("delete/{id}/")
def delete_post(request, id:int):
    try:
        post = Post.objects.get(id=id, author=request.auth)
        post.delete()
        return {"message": f"Deleted post '{post.title}' successfully"}
    except Post.DoesNotExist:
        return {"error": "Post not found or you do not have permission"}
