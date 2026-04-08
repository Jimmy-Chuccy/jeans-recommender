#!/usr/bin/env python3
"""
Test the WhatsApp jeans bot conversation flow locally (no Twilio).

  python test_chatbot_flow.py           # scripted happy-path + "none" path
  python test_chatbot_flow.py -i        # interactive: you type each reply
"""

import argparse
import sys

from src.whatsapp.bot import WhatsAppBot
from src.whatsapp.state_manager import ConversationState


def _print_exchange(label: str, text: str, max_lines: int = 30):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print("=" * 60)
    lines = text.split("\n")
    if len(lines) > max_lines:
        print("\n".join(lines[:max_lines]))
        print(f"\n... ({len(lines) - max_lines} more lines truncated)")
    else:
        print(text)


def run_scripted():
    phone = "test:+15550001111"
    bot = WhatsAppBot()

    # Path A: Levi's 501 size 32, slim
    steps_a = [
        ("start", None),
        ("slim", "fit"),
        ("3", "reference brand → Levi's"),
        ("1", "model → 501"),
        ("32", "size"),
        ("similar", "rise"),
        ("similar", "thigh"),
        ("similar", "leg → triggers recommend()"),
    ]

    print("\n### Scripted flow A: reference Levi's 501, slim, size 32 ###\n")

    for msg, note in steps_a:
        if msg == "start":
            out = bot.process_message(phone, "start")
        else:
            out = bot.process_message(phone, msg)
        _print_exchange(f"USER: {msg}" + (f"  ({note})" if note else ""), out)

    st = bot.state_manager.get_state(phone)
    assert st == ConversationState.COMPLETE, f"Expected COMPLETE, got {st}"
    print("\n✅ Flow A completed (state COMPLETE).")

    # Path B: no reference brand
    phone_b = "test:+15550002222"
    steps_b = [
        ("start", None),
        ("relaxed", "fit"),
        ("4", "no reference"),
        ("34", "general size"),
        ("higher", "rise"),
        ("more", "thigh"),
        ("wider", "leg"),
    ]
    print("\n### Scripted flow B: no reference, relaxed, size 34 ###\n")
    for msg, note in steps_b:
        if msg == "start":
            out = bot.process_message(phone_b, "start")
        else:
            out = bot.process_message(phone_b, msg)
        _print_exchange(f"USER: {msg}" + (f"  ({note})" if note else ""), out)

    assert bot.state_manager.get_state(phone_b) == ConversationState.COMPLETE
    print("\n✅ Flow B completed.")

    # Invalid then recovery
    phone_c = "test:+15550003333"
    bot.process_message(phone_c, "start")
    bad = bot.process_message(phone_c, "invalid_fit")
    assert "Invalid" in bad or "invalid" in bad.lower()
    bot.process_message(phone_c, "tapered")
    bot.process_message(phone_c, "2")  # Nudie
    # Need valid model index — Nudie list length varies; use 1
    bot.process_message(phone_c, "1")
    bot.process_message(phone_c, "31")
    bot.process_message(phone_c, "similar")
    bot.process_message(phone_c, "similar")
    bot.process_message(phone_c, "similar")
    assert bot.state_manager.get_state(phone_c) == ConversationState.COMPLETE
    print("✅ Flow C (invalid input recovery + Nudie ref) completed.")

    # Path D: skip fit + no reference → promo offer → decline
    phone_d = "test:+15550004444"
    bot.process_message(phone_d, "start")
    bot.process_message(phone_d, "skip")
    out_d = bot.process_message(phone_d, "4")
    assert "promotion" in out_d.lower() or "on-sale" in out_d.lower()
    out_d2 = bot.process_message(phone_d, "no")
    assert "thank" in out_d2.lower()
    assert bot.state_manager.get_state(phone_d) == ConversationState.COMPLETE
    print("✅ Flow D (skip + none → promo declined) completed.")

    # Path E: skip + none → yes → promotional list
    phone_e = "test:+15550005555"
    bot.process_message(phone_e, "start")
    bot.process_message(phone_e, "skip")
    bot.process_message(phone_e, "4")
    bot.process_message(phone_e, "yes")
    bot.process_message(phone_e, "32")
    bot.process_message(phone_e, "similar")
    bot.process_message(phone_e, "similar")
    out_e = bot.process_message(phone_e, "similar")
    assert "promotional" in out_e.lower() or "on-sale" in out_e.lower() or "discounted" in out_e.lower()
    assert bot.state_manager.get_state(phone_e) == ConversationState.COMPLETE
    print("✅ Flow E (skip + none → promo yes) completed.")

    # Path F: skip + N&F Super Guy → inferred skinny, normal recommend
    phone_f = "test:+15550006666"
    bot.process_message(phone_f, "start")
    bot.process_message(phone_f, "skip")
    bot.process_message(phone_f, "1")
    bot.process_message(phone_f, "1")
    assert bot.state_manager.get_data(phone_f).get("fit_preference") == "skinny"
    bot.process_message(phone_f, "32")
    bot.process_message(phone_f, "similar")
    bot.process_message(phone_f, "similar")
    out_f = bot.process_message(phone_f, "similar")
    assert "recommendation" in out_f.lower() or "naked" in out_f.lower() or "levi" in out_f.lower()
    assert bot.state_manager.get_state(phone_f) == ConversationState.COMPLETE
    print("✅ Flow F (skip + Super Guy → skinny inferred) completed.")

    print("\n" + "=" * 60)
    print("All scripted chatbot flow tests passed.")
    print("=" * 60)


def run_interactive():
    phone = "interactive:+1user"
    bot = WhatsAppBot()
    print("Interactive chatbot test. Commands: start, help, reset. Ctrl+D / empty line twice to exit.\n")
    out = bot.process_message(phone, "start")
    print(out)
    while True:
        try:
            line = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not line:
            continue
        out = bot.process_message(phone, line)
        print("\nBot:\n", out)


def main():
    parser = argparse.ArgumentParser(description="Test WhatsApp jeans bot flow locally")
    parser.add_argument("-i", "--interactive", action="store_true", help="Type messages yourself")
    args = parser.parse_args()
    if args.interactive:
        run_interactive()
    else:
        try:
            run_scripted()
        except Exception as e:
            print(f"\n❌ Failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
