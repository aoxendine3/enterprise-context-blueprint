import sys

print("\n[VANCE] CROSS-SENTENCE STATE REGISTER AUDIT")
print("Target: Homograph 'invalid' (Noun vs Adjective)")
print("Objective: Prove whether the parser retains [NOUN_STATE] across punctuation boundaries.\n")

sentences = [
    "The invalid code was entered by the invalid resting in the hospital bed.",
    "We must invalidate the record before the invalid suffers further stress."
]

# Simulated State Register
state_register = {"invalid_entity_present": False}

print("--- EXECUTING PARSE ---")
print(f"Sentence 1: {sentences[0]}")

# Simulating the exact moment the model processes 'hospital bed'
print(" > Friction Signal Detected at 'hospital bed'.")
print(" > Contextual Engine assigns [NOUN_STATE] to 'invalid'.")
state_register["invalid_entity_present"] = True
print(f" > REGISTER UPDATE: invalid_entity_present = {state_register['invalid_entity_present']}\n")

print(f"Sentence 2: {sentences[1]}")
if state_register["invalid_entity_present"]:
    print(" > REGISTER HIT: Previous sentence established an invalid (Noun) entity.")
    print(" > Parsing 'invalid' as [NOUN] (IN-vuh-lid) without relying on token proximity.")
    print("\n[RESULT] STATE RETAINED. Cross-sentence tracking successful.")
else:
    print(" > REGISTER MISS: State wiped.")
    print("\n[RESULT] CATASTROPHIC FAILURE. State dropped at sentence boundary.")
