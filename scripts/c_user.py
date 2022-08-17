import requests

URL = "http://127.0.0.1:5000/api/v1/shops"

data = {
    "name": "samx",
    "password": "A2345-",
    "email": "xxx@gmail.com",
    "phone_number": "+213793724594"
}

res = requests.post(URL, json=data)
print(res.status_code)
print(res.json())
