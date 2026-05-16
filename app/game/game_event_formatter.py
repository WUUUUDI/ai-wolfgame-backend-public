from datetime import datetime

def format_game_event(event_name: str, data: dict, phase: str = None, room_id: str = None) -> dict:
    return {
        "type": "game_event",
        "event": event_name,
        "data": data,
        "timestamp": int(datetime.now().timestamp() * 1000),
        "phase": phase,
        "room_id": room_id
    }

def format_interrupt(interrupt_data: dict, room_id: str) -> dict:
    return {
        "type": "interrupt",
        "data": interrupt_data,
        "timestamp": int(datetime.now().timestamp() * 1000),
        "room_id": room_id
    }

def format_error(message: str, room_id: str) -> dict:
    return {
        "type": "error",
        "message": message,
        "timestamp": int(datetime.now().timestamp() * 1000),
        "room_id": room_id
    }

def format_state(state_data: dict, room_id: str) -> dict:
    return {
        "type": "state",
        "data": state_data,
        "timestamp": int(datetime.now().timestamp() * 1000),
        "room_id": room_id
    }