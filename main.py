from datetime import date
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fade_ai import run_fade_chat_turn

load_dotenv()

app = FastAPI(
    title="Fade Barber Assistant API Portal",
    version="2.0"
)


class ChatMessageInput(BaseModel):
    user_message: str
    phone_number: str
    chat_history: Optional[List[dict]] = []


@app.get("/")
def home_health_check():
    return {
        "status": "ONLINE",
        "service": "Fade AI Automation Core Framework"
    }


@app.post("/webhook/fade")
def handle_incoming_customer_text(payload: ChatMessageInput):
    print(f"📥 Message from {payload.phone_number}: {payload.user_message}")

    today_str = date.today().strftime("%Y-%m-%d")
    enriched_message = f"[Today's date is {today_str}] {payload.user_message}"

    ai_response = run_fade_chat_turn(
        enriched_message,
        payload.phone_number,
        payload.chat_history
    )

    if ai_response["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=ai_response["reply_text"]
        )

    return ai_response