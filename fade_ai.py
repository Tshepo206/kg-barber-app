import os
from datetime import date, datetime, timedelta

import psycopg2
from dotenv import load_dotenv
from psycopg2.errors import UniqueViolation

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

MAIN_MENU = "main_menu"
SERVICE_MENU = "service_menu"
DAY_MENU = "day_menu"
TIME_MENU = "time_menu"
ASK_NAME = "ask_name"
CONFIRM_BOOKING = "confirm_booking"

SERVICES = {
    "1": "Haircut",
    "2": "Kiddies cut",
    "3": "Shaving",
    "4": "Blade cut",
    "5": "Hair dye",
    "6": "Bleach",
    "7": "Powder",
}

SHOP_TIMES = ["10:00", "11:30", "14:00", "16:30"]

YES_WORDS = {"yes", "y", "confirm", "book", "book it", "lock it in", "ok", "okay"}
CHANGE_WORDS = {"no", "n", "change", "cancel", "restart", "start over", "menu"}


def reply(text: str):
    return {
        "status": "reply",
        "reply_text": text,
    }


def normalize_message(user_message: str) -> str:
    clean_message = user_message.lower().strip()

    if "]" in clean_message:
        clean_message = clean_message.split("]")[-1].strip()

    return clean_message


def get_db_connection():
    return psycopg2.connect(DB_URL)


def db_get_available_times(target_date: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT booking_time
            FROM bookings
            WHERE booking_date = %s
            AND status = 'Confirmed';
            """,
            (target_date,),
        )

        booked_times = {str(row[0])[:5] for row in cursor.fetchall()}

        return [
            slot for slot in SHOP_TIMES
            if slot not in booked_times
        ]

    except Exception as e:
        print(f"DB Available Times Error: {e}")
        return SHOP_TIMES

    finally:
        cursor.close()
        conn.close()


def db_create_booking(
    phone_number: str,
    full_name: str,
    target_date: str,
    target_time: str,
    service: str,
) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO clients (
                phone_number,
                full_name,
                last_service,
                last_visit_date,
                total_bookings
            )
            VALUES (%s, %s, %s, %s, 1)
            ON CONFLICT (phone_number)
            DO UPDATE SET
                full_name = EXCLUDED.full_name,
                last_service = EXCLUDED.last_service,
                last_visit_date = EXCLUDED.last_visit_date,
                total_bookings = clients.total_bookings + 1;
            """,
            (phone_number, full_name, service, target_date),
        )

        cursor.execute(
            """
            INSERT INTO bookings (
                phone_number,
                booking_date,
                booking_time,
                service_type,
                status
            )
            VALUES (%s, %s, %s, %s, 'Confirmed');
            """,
            (phone_number, target_date, target_time, service),
        )

        conn.commit()
        return "SUCCESS"

    except UniqueViolation:
        conn.rollback()
        return "SLOT_TAKEN"

    except Exception as e:
        conn.rollback()
        print(f"DB Booking Error: {e}")
        return "FAILED"

    finally:
        cursor.close()
        conn.close()


def db_get_customer(phone_number: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT full_name, last_service, last_visit_date, total_bookings
            FROM clients
            WHERE phone_number = %s;
            """,
            (phone_number,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "full_name": row[0],
            "last_service": row[1],
            "last_visit_date": str(row[2]) if row[2] else None,
            "total_bookings": row[3],
        }

    finally:
        cursor.close()
        conn.close()


def db_get_state(phone_number: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                full_name,
                service_type,
                booking_date,
                booking_time,
                awaiting_confirmation,
                step
            FROM conversation_state
            WHERE phone_number = %s;
            """,
            (phone_number,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "full_name": row[0],
            "service_type": row[1],
            "booking_date": str(row[2]) if row[2] else None,
            "booking_time": str(row[3])[:5] if row[3] else None,
            "awaiting_confirmation": row[4],
            "step": row[5],
        }

    finally:
        cursor.close()
        conn.close()


def db_save_state(
    phone_number: str,
    full_name: str = None,
    service_type: str = None,
    booking_date: str = None,
    booking_time: str = None,
    awaiting_confirmation: bool = False,
    step: str = MAIN_MENU,
):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO conversation_state (
                phone_number,
                full_name,
                service_type,
                booking_date,
                booking_time,
                awaiting_confirmation,
                step,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (phone_number)
            DO UPDATE SET
                full_name = EXCLUDED.full_name,
                service_type = EXCLUDED.service_type,
                booking_date = EXCLUDED.booking_date,
                booking_time = EXCLUDED.booking_time,
                awaiting_confirmation = EXCLUDED.awaiting_confirmation,
                step = EXCLUDED.step,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (
                phone_number,
                full_name,
                service_type,
                booking_date,
                booking_time,
                awaiting_confirmation,
                step,
            ),
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()


def db_clear_state(phone_number: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM conversation_state WHERE phone_number = %s;",
            (phone_number,),
        )
        conn.commit()

    finally:
        cursor.close()
        conn.close()


def main_menu_message():
    return (
        "Yoh! This is Fade, KG Barber's AI booking assistant.\n\n"
        "What can I help you with today?\n\n"
        "1 — Book an appointment\n"
        "2 — Reschedule\n"
        "3 — Cancel"
    )


def service_menu_message():
    return (
        "Sharp. What are you booking?\n\n"
        "1 — Haircut\n"
        "2 — Kiddies cut\n"
        "3 — Shaving\n"
        "4 — Blade cut\n"
        "5 — Hair dye\n"
        "6 — Bleach\n"
        "7 — Powder"
    )


def get_next_7_days():
    today = date.today()
    days = []

    for i in range(7):
        target_day = today + timedelta(days=i)

        label = (
            f"Today, {target_day.strftime('%A %d %b')}"
            if i == 0
            else target_day.strftime("%A %d %b")
        )

        days.append(
            {
                "option": str(i + 1),
                "date": target_day.strftime("%Y-%m-%d"),
                "display": label,
            }
        )

    return days


def day_menu_message():
    lines = [
        "You can book up to 7 days ahead.",
        "",
        "Which day works best?",
        "",
    ]

    for day in get_next_7_days():
        lines.append(f"{day['option']} — {day['display']}")

    return "\n".join(lines)


def time_menu_message(target_date: str):
    available_times = db_get_available_times(target_date)

    if not available_times:
        return (
            "Eish, that day is fully booked.\n\n"
            "Please choose another day."
        )

    display_date = datetime.strptime(target_date, "%Y-%m-%d").strftime("%A %d %b")

    lines = [
        f"These times are open on {display_date}:",
        "",
    ]

    for index, slot in enumerate(available_times, start=1):
        lines.append(f"{index} — {slot}")

    lines.append("")
    lines.append("Which one works?")

    return "\n".join(lines)


def confirmation_message(state):
    display_date = datetime.strptime(
        state["booking_date"],
        "%Y-%m-%d",
    ).strftime("%A %d %b")

    return (
        "Just to confirm:\n\n"
        f"Name: {state['full_name']}\n"
        f"Service: {state['service_type']}\n"
        f"Date: {display_date}\n"
        f"Time: {state['booking_time']}\n\n"
        "Reply YES to lock it in, or CHANGE to start again."
    )


def confirmed_message(state):
    display_date = datetime.strptime(
        state["booking_date"],
        "%Y-%m-%d",
    ).strftime("%A %d %b")

    return (
        "Confirmed! Here's your booking:\n\n"
        f"Name: {state['full_name']}\n"
        f"Service: {state['service_type']}\n"
        f"Date: {display_date} at {state['booking_time']}\n\n"
        "I'll remind you Friday evening. See you then! ✂️\n\n"
        "Prices here: https://your-price-list-link.com"
    )


def start_new_flow(phone_number: str, customer=None):
    full_name = customer["full_name"] if customer else None

    db_save_state(
        phone_number=phone_number,
        full_name=full_name,
        service_type=None,
        booking_date=None,
        booking_time=None,
        awaiting_confirmation=False,
        step=MAIN_MENU,
    )

    return reply(main_menu_message())


def handle_main_menu(clean_message, phone_number, state):
    if clean_message == "1":
        db_save_state(
            phone_number=phone_number,
            full_name=state.get("full_name"),
            service_type=None,
            booking_date=None,
            booking_time=None,
            awaiting_confirmation=False,
            step=SERVICE_MENU,
        )
        return reply(service_menu_message())

    if clean_message == "2":
        return reply("No stress. Rescheduling is coming next.")

    if clean_message == "3":
        return reply("Sorted. Cancellations are coming next.")

    return reply(main_menu_message())


def handle_service_menu(clean_message, phone_number, state):
    if clean_message not in SERVICES:
        return reply(service_menu_message())

    db_save_state(
        phone_number=phone_number,
        full_name=state.get("full_name"),
        service_type=SERVICES[clean_message],
        booking_date=None,
        booking_time=None,
        awaiting_confirmation=False,
        step=DAY_MENU,
    )

    return reply(day_menu_message())


def handle_day_menu(clean_message, phone_number, state):
    valid_options = {day["option"]: day for day in get_next_7_days()}

    if clean_message not in valid_options:
        return reply(day_menu_message())

    booking_date = valid_options[clean_message]["date"]
    available_times = db_get_available_times(booking_date)

    if not available_times:
        db_save_state(
            phone_number=phone_number,
            full_name=state.get("full_name"),
            service_type=state.get("service_type"),
            booking_date=None,
            booking_time=None,
            awaiting_confirmation=False,
            step=DAY_MENU,
        )

        return reply(
            "Eish, that day is fully booked.\n\n"
            + day_menu_message()
        )

    db_save_state(
        phone_number=phone_number,
        full_name=state.get("full_name"),
        service_type=state.get("service_type"),
        booking_date=booking_date,
        booking_time=None,
        awaiting_confirmation=False,
        step=TIME_MENU,
    )

    return reply(time_menu_message(booking_date))


def handle_time_menu(clean_message, phone_number, state):
    available_times = db_get_available_times(state["booking_date"])

    valid_options = {
        str(index): slot
        for index, slot in enumerate(available_times, start=1)
    }

    if clean_message not in valid_options:
        return reply(time_menu_message(state["booking_date"]))

    selected_time = valid_options[clean_message]

    next_step = CONFIRM_BOOKING if state.get("full_name") else ASK_NAME

    db_save_state(
        phone_number=phone_number,
        full_name=state.get("full_name"),
        service_type=state.get("service_type"),
        booking_date=state.get("booking_date"),
        booking_time=selected_time,
        awaiting_confirmation=(next_step == CONFIRM_BOOKING),
        step=next_step,
    )

    updated_state = db_get_state(phone_number)

    if next_step == ASK_NAME:
        return reply("Cool. What name should I put on the booking?")

    return reply(confirmation_message(updated_state))


def handle_ask_name(clean_message, phone_number, state):
    if len(clean_message) < 2:
        return reply("Please send the name for the booking.")

    full_name = clean_message.title()

    db_save_state(
        phone_number=phone_number,
        full_name=full_name,
        service_type=state.get("service_type"),
        booking_date=state.get("booking_date"),
        booking_time=state.get("booking_time"),
        awaiting_confirmation=True,
        step=CONFIRM_BOOKING,
    )

    updated_state = db_get_state(phone_number)
    return reply(confirmation_message(updated_state))


def handle_confirmation(clean_message, phone_number, state):
    if clean_message in CHANGE_WORDS:
        db_clear_state(phone_number)
        return start_new_flow(phone_number)

    if clean_message not in YES_WORDS:
        return reply("Reply YES to lock it in, or CHANGE to start again.")

    result = db_create_booking(
        phone_number=phone_number,
        full_name=state["full_name"],
        target_date=state["booking_date"],
        target_time=state["booking_time"],
        service=state["service_type"],
    )

    if result == "SUCCESS":
        final_message = confirmed_message(state)
        db_clear_state(phone_number)
        return reply(final_message)

    if result == "SLOT_TAKEN":
        db_save_state(
            phone_number=phone_number,
            full_name=state.get("full_name"),
            service_type=state.get("service_type"),
            booking_date=state.get("booking_date"),
            booking_time=None,
            awaiting_confirmation=False,
            step=TIME_MENU,
        )

        return reply(
            "That slot just got taken.\n\n"
            + time_menu_message(state["booking_date"])
        )

    return reply("Sorry, I had trouble saving that booking. Please try again.")


def run_fade_chat_turn(
    user_message: str,
    phone_number: str,
    chat_history: list = None,
):
    try:
        clean_message = normalize_message(user_message)
        customer = db_get_customer(phone_number)
        state = db_get_state(phone_number)

        print("========== FADE TURN ==========")
        print("DEBUG user_message:", user_message)
        print("DEBUG clean_message:", clean_message)
        print("DEBUG phone_number:", phone_number)
        print("DEBUG state:", state)
        print("===============================")

        if clean_message in {"hi", "hello", "hey", "start", "restart", "reset", "menu"}:
            db_clear_state(phone_number)
            return start_new_flow(phone_number, customer)

        if not state:
            return start_new_flow(phone_number, customer)

        step = state.get("step") or MAIN_MENU

        if step == MAIN_MENU:
            return handle_main_menu(clean_message, phone_number, state)

        if step == SERVICE_MENU:
            return handle_service_menu(clean_message, phone_number, state)

        if step == DAY_MENU:
            return handle_day_menu(clean_message, phone_number, state)

        if step == TIME_MENU:
            return handle_time_menu(clean_message, phone_number, state)

        if step == ASK_NAME:
            return handle_ask_name(clean_message, phone_number, state)

        if step == CONFIRM_BOOKING:
            return handle_confirmation(clean_message, phone_number, state)

        db_clear_state(phone_number)
        return start_new_flow(phone_number, customer)

    except Exception as e:
        print(f"FADE ERROR: {e}")
        return {
            "status": "error",
            "reply_text": f"Fade Core Framework Offline: {str(e)}",
        }