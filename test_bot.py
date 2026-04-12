import requests
try:
    response = requests.post("http://localhost:8000/api/chat", json={"message": "Tomato price", "language": "en"})
    print("Status:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)
