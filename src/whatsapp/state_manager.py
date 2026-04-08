"""
State management for WhatsApp conversations
Tracks user progress through the recommendation flow
"""

from typing import Dict, Optional, List
from enum import Enum


class ConversationState(Enum):
    """States in the conversation flow"""
    START = "start"
    WAITING_FIT = "waiting_fit"
    WAITING_REFERENCE_BRAND = "waiting_reference_brand"
    WAITING_PROMO_OFFER = "waiting_promo_offer"  # skip fit + no reference: offer on-sale picks
    WAITING_REFERENCE_MODEL = "waiting_reference_model"   # which fit/model from that brand (or skip if "none")
    WAITING_REFERENCE_SIZE = "waiting_reference_size"
    WAITING_RISE = "waiting_rise"
    WAITING_THIGH = "waiting_thigh"
    WAITING_LEG_OPENING = "waiting_leg_opening"
    COMPLETE = "complete"


class StateManager:
    """
    Manages conversation state for each user (identified by phone number)
    In-memory storage for PoC - use Redis/database for production
    """

    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    def get_state(self, phone_number: str) -> ConversationState:
        if phone_number not in self._sessions:
            return ConversationState.START
        state_str = self._sessions[phone_number].get("state", ConversationState.START.value)
        return ConversationState(state_str)

    def set_state(self, phone_number: str, state: ConversationState, data: Optional[Dict] = None):
        if phone_number not in self._sessions:
            self._sessions[phone_number] = {"state": state.value, "data": {}}
        self._sessions[phone_number]["state"] = state.value
        if data:
            self._sessions[phone_number]["data"].update(data)

    def get_data(self, phone_number: str) -> Dict:
        if phone_number not in self._sessions:
            return {}
        return self._sessions[phone_number].get("data", {})

    def update_data(self, phone_number: str, **kwargs):
        if phone_number not in self._sessions:
            self._sessions[phone_number] = {"state": ConversationState.START.value, "data": {}}
        self._sessions[phone_number]["data"].update(kwargs)

    def reset(self, phone_number: str):
        if phone_number in self._sessions:
            del self._sessions[phone_number]

    def get_all_data(self, phone_number: str) -> Dict:
        if phone_number not in self._sessions:
            return {"state": ConversationState.START.value, "data": {}}
        return self._sessions[phone_number].copy()
