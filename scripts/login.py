import requests

URL = "http://127.0.0.1:5000/api/v1/login"

data = {
    "password": "A2345-",
    "email": "xxx@gmail.com",
}

res = requests.post(URL, json=data)
print(res.status_code)
print(res.json())
