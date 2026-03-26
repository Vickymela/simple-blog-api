from ninja import Schema,ModelSchema

from .models import Post


class userinputschema(Schema):
      username:str
      email:str
      password:str
class userloginschema(Schema):
         username:str
         password:str

class PostSchemaInput(Schema):
        title: str  
        content: str

class PostSchemaOutput(Schema):
        title: str
        content: str
        author: str

class UpdateSchema(Schema):
        title: str
        content: str
        # author: str


# class AuthorSchema(Schema):
#     id: int
#     username: str
#     email: str

# class CreatePostSchema(Schema):
#     title: str
#     content: str
#     author: AuthorSchema

# class UserSchema(Schema):
#     id: int
#     username: str
#     email: str





       


