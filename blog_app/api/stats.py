from ninja import Router

main_api = Router(tags=["Stats"])


@main_api.get("stats/")
def get_stats(request):
    return {"message": "This is the stats endpoint"}
