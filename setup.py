import requests
import time

# requests.post("http://127.0.0.1:5000/join", json={"port": "5000"})
# time.sleep(1)
# requests.post("http://127.0.0.1:5001/join", json={"port": "5000"})
# time.sleep(1)
# requests.post("http://127.0.0.1:5003/join", json={"port": "5000"})
# time.sleep(1)
# requests.post("http://127.0.0.1:5004/join", json={"port": "5000"})
# time.sleep(1)

# requests.post("http://127.0.0.1:5000/store?key=1&value=a")
# time.sleep(1)
# requests.post("http://127.0.0.1:5000/store?key=2&value=b")
# time.sleep(1)
# requests.post("http://127.0.0.1:5000/store?key=3&value=c")
# time.sleep(1)

requests.post("http://127.0.0.1:5002/join", json={"port": "5000"})
time.sleep(1)
requests.post("http://127.0.0.1:5005/join", json={"port": "5000"})
time.sleep(1)