# ============================================================
# FILE: user_manager.py
# PURPOSE: User registration, unique IDs, session + chat history
# STORAGE: Google Sheets tabs — users | chat_history
# ============================================================

import re
import random
from datetime import datetime

USERS_SHEET = "users"
CHAT_SHEET  = "chat_history"


# ════════════════════════════════════════════════════════════
# FUNCTION 1: Generate memorable unique ID
# ════════════════════════════════════════════════════════════
def generate_user_id(name="", contact=""):
    """
    Generates a short, memorable Eco AI user ID.

    WITH contact  → eco-{last 4 digits}
        e.g. contact +923359997679  → eco-7679

    WITHOUT contact → eco-{first_letter}{position_of_first_letter}{last_letter}
        e.g. name "Suhani"
            first letter : s  (position 19 in alphabet)
            last letter  : i
            result       : eco-s19i

    Args:
        name    : user's name string
        contact : phone/contact string (digits only, optional)

    Returns:
        ID string e.g. "eco-7679" or "eco-s19i"
    """
    # ── WITH contact ──────────────────────────────────────────
    if contact:
        digits = re.sub(r"\D", "", contact)   # strip non-digits
        if len(digits) >= 4:
            return f"eco-{digits[-4:]}"

    # ── WITHOUT contact ───────────────────────────────────────
    clean = name.strip().lower()
    if len(clean) >= 2:
        first    = clean[0]                                    # e.g. 's'
        last     = clean[-1]                                   # e.g. 'i'
        position = ord(first) - ord('a') + 1                  # s → 19
        return f"eco-{first}{position}{last}"

    # Fallback: eco + 4 random digits
    return f"eco-{random.randint(1000,9999)}"


# ════════════════════════════════════════════════════════════
# FUNCTION 2: Ensure required sheet tabs exist
# ════════════════════════════════════════════════════════════
def ensure_sheets(sheet):
    existing = [ws.title for ws in sheet.worksheets()]

    if USERS_SHEET not in existing:
        ws = sheet.add_worksheet(title=USERS_SHEET, rows=1000, cols=11)
        ws.append_row(["user_id","name","city","contact","registered_at",
                       "last_seen","total_scans","language"])

    if CHAT_SHEET not in existing:
        ws = sheet.add_worksheet(title=CHAT_SHEET, rows=5000, cols=8)
        ws.append_row(["timestamp","user_id","user_name","role",
                       "message","waste_type","language","session_id"])


# ════════════════════════════════════════════════════════════
# FUNCTION 3: Register new user
# ════════════════════════════════════════════════════════════
def register_new_user(db, name, city, contact="", language="english"):
    """
    Creates a new user, saves to Sheets, returns user dict.

    Args:
        name    : user's full name
        city    : user's city
        contact : phone number (optional — used for ID generation)
        language: preferred language

    Returns:
        user dict with user_id, name, city, contact, etc.
        or None if failed
    """
    sheet = db.get("sheet")
    if not sheet:
        return None

    try:
        ensure_sheets(sheet)
        ws       = sheet.worksheet(USERS_SHEET)
        existing = [r[0] for r in ws.get_all_values()[1:] if r]

        # Generate ID using name + contact
        uid = generate_user_id(name=name, contact=contact)

        # If collision, append random 2-digit suffix
        if uid in existing:
            uid = f"{uid}-{random.randint(10,99)}"

        now = datetime.now().isoformat()
        ws.append_row([uid, name, city, contact, now, now, 0, language])

        print(f"✅ Registered: {name} → {uid}")
        return {"user_id":uid,"name":name,"city":city,"contact":contact,
                "registered_at":now,"last_seen":now,
                "total_scans":0,"language":language,"is_new":True}

    except Exception as e:
        print(f"❌ Register failed: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 4: Find returning user
# ════════════════════════════════════════════════════════════
def find_user(db, user_id=None, name=None):
    """
    Finds user by ID (exact) or name (case-insensitive).

    Returns:
        user dict or None if not found
    """
    sheet = db.get("sheet")
    if not sheet:
        return None

    try:
        ws      = sheet.worksheet(USERS_SHEET)
        rows    = ws.get_all_values()
        if len(rows) <= 1:
            return None

        headers = rows[0]
        for i, row in enumerate(rows[1:], start=2):
            if not row:
                continue
            padded = row + [""] * (len(headers) - len(row))
            data   = dict(zip(headers, padded))

            id_match   = user_id and data.get("user_id","").strip().upper() == user_id.strip().upper()
            name_match = name and data.get("name","").strip().lower() == name.strip().lower()

            if id_match or (name_match and not user_id):
                # Update last_seen
                try:
                    ws.update_cell(i, headers.index("last_seen") + 1,
                                   datetime.now().isoformat())
                except:
                    pass
                return {
                    "user_id"    : data.get("user_id",""),
                    "name"       : data.get("name",""),
                    "city"       : data.get("city",""),
                    "contact"    : data.get("contact",""),
                    "registered_at": data.get("registered_at",""),
                    "last_seen"  : datetime.now().isoformat(),
                    "total_scans": int(data.get("total_scans",0) or 0),
                    "language"   : data.get("language","english"),
                    "is_new"     : False
                }
        return None

    except Exception as e:
        print(f"❌ Find user failed: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 5: Save chat message
# ════════════════════════════════════════════════════════════
def save_chat_message(db, user, role, message,
                      waste_type="", session_id=""):
    """
    Saves one chat message to Google Sheets chat_history tab.

    Args:
        role    : "user" or "assistant"
        message : message text (truncated to 1000 chars)
    """
    sheet = db.get("sheet")
    if not sheet:
        return
    try:
        ws = sheet.worksheet(CHAT_SHEET)
        ws.append_row([
            datetime.now().isoformat(),
            user.get("user_id",""),
            user.get("name",""),
            role,
            str(message)[:1000],
            waste_type,
            user.get("language","english"),
            session_id
        ])
    except Exception as e:
        print(f"❌ Chat save: {e}")


# ════════════════════════════════════════════════════════════
# FUNCTION 6: Get chat history for user
# ════════════════════════════════════════════════════════════
def get_user_chat_history(db, user_id, limit=30):
    """
    Returns recent chat messages for a user (most recent first).

    Returns:
        list of message dicts
    """
    sheet = db.get("sheet")
    if not sheet:
        return []
    try:
        ws      = sheet.worksheet(CHAT_SHEET)
        rows    = ws.get_all_values()
        if len(rows) <= 1:
            return []
        headers = rows[0]
        msgs    = []
        for row in rows[1:]:
            if not row: continue
            padded = row + [""] * (len(headers) - len(row))
            data   = dict(zip(headers, padded))
            if data.get("user_id","").strip() == user_id.strip():
                msgs.append(data)
        return msgs[-limit:][::-1]
    except Exception as e:
        print(f"❌ Chat history: {e}")
        return []


# ════════════════════════════════════════════════════════════
# FUNCTION 7: Increment scan count
# ════════════════════════════════════════════════════════════
def increment_scan_count(db, user_id):
    """Adds 1 to total_scans for the given user_id."""
    sheet = db.get("sheet")
    if not sheet: return
    try:
        ws      = sheet.worksheet(USERS_SHEET)
        rows    = ws.get_all_values()
        headers = rows[0]
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0].strip() == user_id.strip():
                col   = headers.index("total_scans") + 1
                count = int(row[headers.index("total_scans")] or 0) + 1
                ws.update_cell(i, col, count)
                return
    except Exception as e:
        print(f"❌ Increment scan: {e}")

