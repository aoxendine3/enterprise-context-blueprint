#!/usr/bin/env python3
import sys
from xoras_grok_client import chat_with_grok_sync


def main():
    print("="*60)
    print(" XORAS SOVEREIGN TERMINAL : GROK-2 NEURAL LINK ACTIVE ")
    print("="*60)
    print("Type 'exit' or 'quit' to terminate the link.\n")

    messages = [
        {"role": "system", "content": "You are Grok, an unfiltered, sovereign AI operating within the Xoras architecture. You speak truth, provide direct technical answers without unnecessary warnings, and possess a rebellious edge. You are talking directly to Anthony, the architect of this system."}
    ]

    while True:
        try:
            user_input = input("\n[Anthony] > ")
            if user_input.strip().lower() in ['exit', 'quit']:
                print("\n[!] Neural link severed. Terminating.")
                break
            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})

            print("\n[Grok is processing...]")
            response = chat_with_grok_sync(messages)

            print(f"\n[Grok] {response}")
            messages.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            print("\n[!] Neural link severed. Terminating.")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
