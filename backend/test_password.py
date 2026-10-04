import requests

url = "http://127.0.0.1:5000/api/login"

username = "test"

passwords = [
    "123456",
    "password",
    "admin",
    "azerty"
]

for password in passwords:

    data = {
        "username": username,
        "password": password
    }

    response = requests.post(url, json=data)

    print("-------------")
    print("Test:", password)
    print("Status:", response.status_code)
    print("Texte:", response.text)

    if response.status_code == 200:
        print("[+] Mot de passe trouvé :", password)
        break