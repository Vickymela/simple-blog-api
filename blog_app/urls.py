from ninja import NinjaAPI, Swagger
from ninja.security import HttpBearer
import jwt
from django.conf import settings

from blog_app.api import auth, post, stats
from blog_app.api.auth import User
from blog_app.models import BlackListedToken
    

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

main_api.add_router("/auth/", auth.main_api)
main_api.add_router("/posts/", post.main_api)
main_api.add_router("/stats/", stats.main_api)
