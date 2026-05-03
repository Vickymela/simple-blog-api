from typing import Optional

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
    id: int
    title: str
    content: str
    author: Optional[str] = None
    joined_txt: str

    @staticmethod
    def resolve_joined_txt(obj):
        return f"{obj.title} - {obj.content}"

    @staticmethod
    def resolve_author(obj):
        return obj.author.username if obj.author else None


class UpdateSchema(Schema):
    title: str
    content: str
    # author: str


class TokenSchema(Schema):
    access_token:str
    token_type:str="bearer"

class MessageSchema(Schema):
    message:str
