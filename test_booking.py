import requests

# Dynamically stitching the address string together to bypass the interface clipping glitch
ip_address = "127.0.0.1"
port_number = ":8000"
endpoint_path = "/webhook/fade"

url = "http://" + ip_address + port_number + endpoint_path

# The mock customer chat message payload data parameters
payload = {
    "user_message": "Hey Fade! I want to confirm a skin fade appointment for my friend David Miller. His phone number is +27829990000. Can you lock him in for 2026-06-15 at 14:00?"
}

print("🔄 Sending mock WhatsApp booking request to Fade...")

try:
    response = requests.post(url, json=payload)
    print("\n🤖 Fade's Automated System Reply:")
    print(response.json()["reply_text"])
except Exception as e:
    print(f"\n❌ Connection Failed: {e}")
    print("Make sure your uvicorn server is still active in your other VS Code terminal tab!")
