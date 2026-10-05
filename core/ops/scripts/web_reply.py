import sys, json, os

CHAT_FILE = r"/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/memory/agent_logs/web_chat.json"
agent = sys.argv[1]
text = sys.argv[2]

try:
    with open(CHAT_FILE, 'r') as f:
        chat = json.load(f)
except:
    chat = []

chat.append({"sender": agent, "text": text})

with open(CHAT_FILE, 'w') as f:
    json.dump(chat, f)
