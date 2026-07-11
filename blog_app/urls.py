from ninja import NinjaAPI, Swagger

from blog_app.utils import AuthBearer

from .api.auth import auth_api
from .api.post import post_api
from .api.sub import sub_api

main_api = NinjaAPI(auth=[AuthBearer()], docs=Swagger(settings={"persistAuthorization": True}))


main_api.add_router("/auth/", router=auth_api)
main_api.add_router("/posts/", router=post_api)
# main_api.add_router("/subscriptions/", router=sub_api)
