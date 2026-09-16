import os, sys, json, time
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STAGE_DIR = SCRIPT_DIR
TIMING_JSON = os.path.join(STAGE_DIR, 'current_timing.json')
STATE_FILE = os.path.join(STAGE_DIR, 'current_image.txt')
TRANSCRIPT_FILE = os.path.join(STAGE_DIR, 'current_transcript.txt')

def speak_sapi(agent_id, text):
    lower_agent = agent_id.lower()
    words = text.split()
    total_chars = sum(len(w) for w in words) if words else 1
    total_duration = max(1.5, len(words) * 0.35)
    word_timings = []
    current_offset = 0.0
    for w in words:
        dur = max(0.18, (len(w) / total_chars) * total_duration)
        word_timings.append({'word': w, 'start': round(current_offset, 2), 'end': round(current_offset + dur, 2)})
        current_offset += dur
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        f.write(lower_agent)
    with open(TRANSCRIPT_FILE, 'w', encoding='utf-8') as f:
        f.write(text)
    playback_start = time.time() + 0.04
    broadcast_data = {'agent': lower_agent, 'text': text, 'start_time': playback_start, 'total_duration': round(total_duration, 2), 'words': word_timings, 'synthesizing': False, 'complete': False}
    with open(TIMING_JSON, 'w', encoding='utf-8') as f:
        json.dump(broadcast_data, f)
    try:
        import win32com.client
        speaker = win32com.client.Dispatch('SAPI.SpVoice')
        speaker.Speak(text)
    except Exception as e:
        print(e)
    broadcast_data['complete'] = True
    with open(TIMING_JSON, 'w', encoding='utf-8') as f:
        json.dump(broadcast_data, f)

if __name__ == '__main__':
    ag = sys.argv[1] if len(sys.argv) > 1 else 'maxx'
    tx = sys.argv[2] if len(sys.argv) > 2 else 'Maxx operational on Sovereign Stage.'
    speak_sapi(ag, tx)
