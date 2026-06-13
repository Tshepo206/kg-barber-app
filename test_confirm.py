import requests

# Dynamically stitching your specific live public ngrok tunnel address path
subdomain = "willing-unmixed-napped"
domain_suffix = ".ngrok-free.dev"
endpoint_route = "/webhook/fade"

url = "https://" + subdomain + domain_suffix + endpoint_route

# Simulating a multi-turn chat history exactly like our successful local test
simulated_chat_history = [
    {
        "role": "user", 
        "content": "Hey Fade! Can I book a skin fade for David Miller (+27633732733) on 2026-06-15 at 16:00?"
    },
    {
        "role": "assistant", 
        "content": "Great news! 15:00 on 2026-06-15 is currently wide open. Shall I lock that slot down for you?"
    }
]

payload = {
    "user_message": "Yes, please confirm it and lock it in right now!",
    "chat_history": simulated_chat_history
}

print("🌐 Streaming data payload over the public internet via ngrok...")

try:
    response = requests.post(url, json=payload)
    print("\n🤖 Fade's Automated Live Cloud Reply:")
    print(response.json())
except Exception as e:
    print(f"\n❌ Public Network Transmission Failed: {e}")
    print("Make sure your ngrok window is still open and running on your desktop screen!")