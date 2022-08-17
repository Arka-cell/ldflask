import requests

URL = "http://127.0.0.1:5000/api/v1/shops"

res = requests.get(URL)
print(res.status_code)
print(res.json())