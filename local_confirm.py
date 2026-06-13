import requests

# Stitching local route parameters to prevent interface clipping glitches
localhost_ip = "127.0.0.1"
server_port = ":8000"
webhook_route = "/webhook/fade"

url = "http://" + localhost_ip + server_port + webhook_route

# SIMULATING MULTI-TURN CHAT HISTORY
# We include Fade's previous offer in the history list to break the checking loop!
simulated_chat_history = [
    {
        "role": "user", 
        "content": "Hey Fade! Can I book a skin fade for David Miller (+27633732733) on 2026-06-15 at 15:00?"
    },
    {
        "role": "assistant", 
        "content": "Great news! 15:00 on 2026-06-15 is currently wide open. Shall I lock that slot down for you?"
    }
]

# The definitive high-intent response from David to trigger the database write function tool
payload = {
    "user_message": "Yes, please confirm it and lock it in right now!",
    "chat_history": simulated_chat_history
}

print("🔄 Sending multi-turn confirmation request directly to local server...")

try:
    response = requests.post(url, json=payload)
    print("\n🤖 Fade's Automated Core System Reply:")
    print(response.json())
except Exception as e:
    print(f"\n❌ Local Connection Failed: {e}")
