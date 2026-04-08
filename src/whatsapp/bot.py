"""
WhatsApp bot logic for the jeans recommendation flow
"""

from typing import Optional, Tuple
from .state_manager import StateManager, ConversationState
from .formatter import (
    format_welcome_message,
    format_reference_brand_question,
    format_reference_model_question,
    format_no_reference_size_question,
    format_reference_size_question,
    format_rise_question,
    format_thigh_question,
    format_leg_opening_question,
    format_recommendations,
    format_error_message,
    format_invalid_input_message,
    format_help_message,
    format_needs_reference_or_promo_message,
    format_promo_declined_thanks,
    format_promotional_recommendations,
)
from ..recommenders.recommender import recommend
from ..recommenders.promo_recommender import recommend_promotional
from ..recommenders.models import UserInput
from ..recommenders.fit_mapper import get_fit_options_for_brand, infer_fit_preference_from_reference


# Brand labels and internal keys
REFERENCE_BRAND_CHOICES = [
    ("1", "nf", "Naked & Famous"),
    ("2", "nudie", "Nudie Jeans"),
    ("3", "levis", "Levi's"),
    ("4", "none", "None of the above"),
]


class WhatsAppBot:
    VALID_FITS = ["relaxed", "slim", "tapered", "straight", "bootcut", "skinny", "skip"]
    VALID_RISE = ["higher", "lower", "similar"]
    VALID_THIGH = ["more", "less", "similar"]
    VALID_LEG_OPENING = ["wider", "narrower", "similar"]
    VALID_COMMANDS = ["start", "help", "reset"]
    VALID_PROMO_YES = frozenset(
        {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "please", "1"}
    )
    VALID_PROMO_NO = frozenset({"no", "n", "nope", "nah", "2"})

    def __init__(self):
        self.state_manager = StateManager()

    def process_message(self, phone_number: str, message: str) -> str:
        message = message.strip().lower()
        if message in self.VALID_COMMANDS:
            return self._handle_command(phone_number, message)

        state = self.state_manager.get_state(phone_number)
        data = self.state_manager.get_data(phone_number)

        try:
            if state == ConversationState.START:
                return self._handle_start(phone_number)
            elif state == ConversationState.WAITING_FIT:
                return self._handle_fit(phone_number, message)
            elif state == ConversationState.WAITING_REFERENCE_BRAND:
                return self._handle_reference_brand(phone_number, message)
            elif state == ConversationState.WAITING_PROMO_OFFER:
                return self._handle_promo_offer(phone_number, message)
            elif state == ConversationState.WAITING_REFERENCE_MODEL:
                return self._handle_reference_model(phone_number, message)
            elif state == ConversationState.WAITING_REFERENCE_SIZE:
                return self._handle_reference_size(phone_number, message)
            elif state == ConversationState.WAITING_RISE:
                return self._handle_rise(phone_number, message)
            elif state == ConversationState.WAITING_THIGH:
                return self._handle_thigh(phone_number, message)
            elif state == ConversationState.WAITING_LEG_OPENING:
                return self._handle_leg_opening(phone_number, message)
            elif state == ConversationState.COMPLETE:
                return "You already completed a recommendation! Type *start* to begin again."
            else:
                return format_error_message("Unknown state. Type 'start' to begin.")
        except Exception as e:
            return format_error_message(str(e))

    def _handle_command(self, phone_number: str, command: str) -> str:
        if command == "start":
            self.state_manager.reset(phone_number)
            return self._handle_start(phone_number)
        if command == "help":
            return format_help_message()
        if command == "reset":
            self.state_manager.reset(phone_number)
            return "✅ Session reset. Type *start* to begin."
        return format_invalid_input_message("command")

    def _handle_start(self, phone_number: str) -> str:
        self.state_manager.set_state(phone_number, ConversationState.WAITING_FIT)
        return format_welcome_message()

    def _handle_fit(self, phone_number: str, message: str) -> str:
        if message not in self.VALID_FITS:
            return format_invalid_input_message("fit preference", self.VALID_FITS)
        fit_preference = None if message == "skip" else message
        self.state_manager.update_data(phone_number, fit_preference=fit_preference)
        self.state_manager.set_state(phone_number, ConversationState.WAITING_REFERENCE_BRAND)
        return format_reference_brand_question()

    def _handle_reference_brand(self, phone_number: str, message: str) -> str:
        choice = message.strip()
        for num, key, label in REFERENCE_BRAND_CHOICES:
            if choice == num or choice == key:
                self.state_manager.update_data(phone_number, reference_brand=key)
                if key == "none":
                    fit_pref = self.state_manager.get_data(phone_number).get("fit_preference")
                    if fit_pref is None:
                        self.state_manager.set_state(
                            phone_number, ConversationState.WAITING_PROMO_OFFER
                        )
                        return format_needs_reference_or_promo_message()
                    self.state_manager.update_data(phone_number, promotional_flow=False)
                    self.state_manager.set_state(phone_number, ConversationState.WAITING_REFERENCE_SIZE)
                    return format_no_reference_size_question()
                options = get_fit_options_for_brand(key, "mens")
                self.state_manager.update_data(phone_number, reference_fit_options=options)
                self.state_manager.set_state(phone_number, ConversationState.WAITING_REFERENCE_MODEL)
                return format_reference_model_question(label, options)
        return format_invalid_input_message("reference brand", ["1", "2", "3", "4"])

    def _handle_promo_offer(self, phone_number: str, message: str) -> str:
        msg = message.strip().lower()
        if msg in self.VALID_PROMO_YES:
            self.state_manager.update_data(phone_number, promotional_flow=True)
            self.state_manager.set_state(phone_number, ConversationState.WAITING_REFERENCE_SIZE)
            return format_no_reference_size_question()
        if msg in self.VALID_PROMO_NO:
            self.state_manager.set_state(phone_number, ConversationState.COMPLETE)
            return format_promo_declined_thanks()
        return format_invalid_input_message("promotions", ["yes", "no"])

    def _handle_reference_model(self, phone_number: str, message: str) -> str:
        data = self.state_manager.get_data(phone_number)
        options = data.get("reference_fit_options") or []
        msg = message.strip()
        # Try 1-based index
        try:
            idx = int(msg)
            if 1 <= idx <= len(options):
                fit_id = options[idx - 1].get("id", "")
                self.state_manager.update_data(phone_number, reference_fit_or_model=fit_id)
                self._maybe_infer_fit_from_reference(phone_number, fit_id)
                self.state_manager.set_state(phone_number, ConversationState.WAITING_REFERENCE_SIZE)
                return format_reference_size_question()
        except ValueError:
            pass
        # Try match by id or name (case-insensitive)
        for opt in options:
            if opt.get("id", "").lower() == msg or opt.get("name", "").lower() == msg:
                fit_id = opt.get("id", "")
                self.state_manager.update_data(phone_number, reference_fit_or_model=fit_id)
                self._maybe_infer_fit_from_reference(phone_number, fit_id)
                self.state_manager.set_state(phone_number, ConversationState.WAITING_REFERENCE_SIZE)
                return format_reference_size_question()
        return format_invalid_input_message("model/fit", [f"{i+1} or {o.get('name','')}" for i, o in enumerate(options[:5])])

    def _maybe_infer_fit_from_reference(self, phone_number: str, fit_id: str) -> None:
        data = self.state_manager.get_data(phone_number)
        if data.get("fit_preference") is not None:
            return
        brand = data.get("reference_brand")
        inferred = infer_fit_preference_from_reference(brand, fit_id)
        if inferred:
            self.state_manager.update_data(phone_number, fit_preference=inferred)

    def _handle_reference_size(self, phone_number: str, message: str) -> str:
        try:
            size = int(message.strip())
        except ValueError:
            return format_invalid_input_message("size", ["30", "32", "34", "etc."])
        self.state_manager.update_data(phone_number, reference_size=size)
        if "reference_fit_or_model" not in self.state_manager.get_data(phone_number):
            self.state_manager.update_data(phone_number, reference_fit_or_model=None)
        self.state_manager.set_state(phone_number, ConversationState.WAITING_RISE)
        return format_rise_question()

    def _handle_rise(self, phone_number: str, message: str) -> str:
        if message not in self.VALID_RISE:
            return format_invalid_input_message("rise preference", self.VALID_RISE)
        self.state_manager.update_data(phone_number, rise_preference=message)
        self.state_manager.set_state(phone_number, ConversationState.WAITING_THIGH)
        return format_thigh_question()

    def _handle_thigh(self, phone_number: str, message: str) -> str:
        if message not in self.VALID_THIGH:
            return format_invalid_input_message("thigh preference", self.VALID_THIGH)
        self.state_manager.update_data(phone_number, thigh_preference=message)
        self.state_manager.set_state(phone_number, ConversationState.WAITING_LEG_OPENING)
        return format_leg_opening_question()

    def _handle_leg_opening(self, phone_number: str, message: str) -> str:
        if message not in self.VALID_LEG_OPENING:
            return format_invalid_input_message("leg opening preference", self.VALID_LEG_OPENING)
        data = self.state_manager.get_data(phone_number)
        data["leg_opening_preference"] = message
        try:
            if data.get("promotional_flow"):
                recs = recommend_promotional(
                    int(data.get("reference_size", 32)),
                    data.get("rise_preference"),
                    data.get("thigh_preference"),
                    message,
                    gender="mens",
                )
                self.state_manager.set_state(phone_number, ConversationState.COMPLETE)
                return format_promotional_recommendations(recs)
            user_input = UserInput(
                fit_preference=data.get("fit_preference"),
                reference_brand=data.get("reference_brand", "none"),
                reference_fit_or_model=data.get("reference_fit_or_model"),
                reference_size=int(data.get("reference_size", 32)),
                gender="mens",
                rise_preference=data.get("rise_preference"),
                thigh_preference=data.get("thigh_preference"),
                leg_opening_preference=message,
            )
            recommendations = recommend(user_input)
            self.state_manager.set_state(phone_number, ConversationState.COMPLETE)
            return format_recommendations(recommendations)
        except Exception as e:
            return format_error_message(f"Failed to get recommendations: {str(e)}")
