from ninja import Router


sub_api = Router(tags=["subscriptions"])

@sub_api.post("subscribe/")
def subscribe(request, email: str):
    # add to db
    return {"detail":"subscription successful"}
