import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

STORAGE_FILE = "saved_trips_db.json"

CURRENCY_RATES_TO_USD = {
    "USD": 1.0,
    "INR": 0.0119,   # 1 INR ≈ 0.0119 USD (1 USD ≈ 84 INR)
    "EUR": 1.08,
    "JPY": 0.0067,
    "THB": 0.029,
    "GBP": 1.27,
    "AED": 0.272,
    "VND": 0.00004,
}


def convert_currency(amount_local: float, local_currency: str) -> Dict[str, float]:
    """Converts a local currency amount into Local, USD, and INR equivalents."""
    code = local_currency.upper().strip()
    rate_to_usd = CURRENCY_RATES_TO_USD.get(code, 1.0)
    usd_val = round(amount_local * rate_to_usd, 2)
    inr_val = round(usd_val * 84.0, 0)
    return {
        "local": round(amount_local, 2),
        "currency": code,
        "usd": usd_val,
        "inr": int(inr_val),
    }


def _load_disk_db() -> List[Dict[str, Any]]:
    """Loads saved trips from local JSON file if available (ephemeral-safe)."""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_disk_db(trips: List[Dict[str, Any]]) -> None:
    """Persists trips to local JSON file without failing on read-only cloud containers."""
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(trips, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def init_trip_store(session_state: Any) -> None:
    """Initializes simulated DB inside Streamlit session_state backed by local JSON."""
    if "saved_trips" not in session_state:
        session_state.saved_trips = _load_disk_db()


def save_trip(
    session_state: Any,
    preferences: Dict[str, Any],
    itinerary_data: Dict[str, Any],
    trip_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Saves or updates a trip record in the simulated database."""
    init_trip_store(session_state)
    destination = itinerary_data.get("destination", preferences.get("destination", "Custom Trip"))
    trip_id = str(uuid.uuid4())[:8].upper()
    record = {
        "trip_id": trip_id,
        "title": trip_title or f"{destination} ({preferences.get('duration', 3)} Days)",
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "preferences": preferences,
        "itinerary": itinerary_data,
    }
    session_state.saved_trips.insert(0, record)
    _save_disk_db(session_state.saved_trips)
    return record


def delete_trip(session_state: Any, trip_id: str) -> None:
    """Deletes a trip by ID from the simulated database."""
    init_trip_store(session_state)
    session_state.saved_trips = [
        t for t in session_state.saved_trips if t.get("trip_id") != trip_id
    ]
    _save_disk_db(session_state.saved_trips)
