#!/usr/bin/env python3
# Live Lead-9 Triad Deliberation Engine
# Powered by Local Bare-Metal Ollama Fleet (sovereign-hermes and qwen2.5:1.5b)
# Synchronously dispatches to 3D Sovereign Stage (Port 8080) and media director.

import os
import sys
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SPEAK_SCRIPT = ROOT / 'ops' / 'scripts' / 'media_director_agent.py'
JOURNAL_FILE = ROOT / 'memory' / 'journals' / 'agents' / 'lead9_roundtable_journal.jsonl'
TIMING_FILE = ROOT / 'ops' / 'scripts' / 'fullscreen_ui' / 'current_timing.json'

OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'

COUNCIL_MEMBERS = [
    {
        'agent': 'jarvis',
        'role': 'Governance and Oversight Lead',
        'prompt': (
            'You are Jarvis, Governance Lead of the Xoras Sovereign Systems council. '
            'In exactly two sentences, state your empirical audit findings on the new SOVRA engine benchmarks '
            '(307k ops/s AVX2 throughput, 9.7 microsecond Poincare geodesics, zero data loss) '
            'and establish the constitutional mandate for continuous off-grid synchronization between the Windows workstation and Mac M4. '
            'Speak directly to Anthony. Zero corporate fluff.'
        )
    },
    {
        'agent': 'maxx',
        'role': 'Operations and Systems Architecture Lead',
        'prompt': (
            'You are Maxx, Operations and Engineering Lead in Xoras. '
            'In exactly two sentences, state your technical breakdown of the 3,200-byte HexCell stride, '
            'cacheline alignment on bare metal, and why keeping all inference on local weights eliminates cloud vulnerability. '
            'Speak directly to Anthony with seasoned engineering confidence.'
        )
    },
    {
        'agent': 'clara',
        'role': 'Orbital Physics and Mathematical Validation Lead',
        'prompt': (
            'You are Clara, Orbital Physics and Mathematical Validation Lead. '
            'In exactly two sentences, state your mathematical confirmation of the Poincare hyperbolic metric tensor, '
            'why hierarchical knowledge embeds without distortion in negative curvature, and certify GOLDEN-004 status. '
            'Speak with intellectual depth and precision.'
        )
    }
]

def query_local_ollama(model: str, prompt: str) -> str:
    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.3,
            'num_predict': 120
        }
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        headers={'Content-Type': 'application/json'},
        data=json.dumps(payload).encode('utf-8')
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode('utf-8'))
    dt = time.perf_counter() - t0
    text = res.get('response', '').strip()
    text = ' '.join(text.split())
    print(f'[{model}] Generated {len(text)} chars in {dt:.2f}s')
    return text

def broadcast_to_stage(agent: str, text: str):
    words = text.split()
    words_data = []
    accum = 0.0
    time_per_word = 0.28
    for w in words:
        words_data.append({'word': w, 'start': round(accum, 2), 'end': round(accum + time_per_word, 2)})
        accum += time_per_word
    
    timing_payload = {
        'agent': agent,
        'text': text,
        'synthesizing': False,
        'words': words_data,
        'duration': round(accum, 2),
        'timestamp': time.time()
    }
    try:
        TIMING_FILE.write_text(json.dumps(timing_payload, indent=2), encoding='utf-8')
    except Exception as e:
        print(f'[WARN] Failed to write timing payload: {e}')

def speak_turn(agent: str, text: str):
    broadcast_to_stage(agent, text)
    if sys.platform == 'win32':
        try:
            import win32com.client
            voice = win32com.client.Dispatch('SAPI.SpVoice')
            voice.Rate = 0
            voice.Volume = 95
            print(f'>>> [VOICE DISPATCH] {agent.upper()}: {text}')
            voice.Speak(f'{agent}: {text}')
        except Exception as e:
            print(f'[VOICE FALLBACK] SAPI playback error: {e}')
    else:
        import subprocess
        subprocess.run([sys.executable, str(SPEAK_SCRIPT), agent, text], check=False)

def run_live_triad():
    print('=' * 70)
    print('XORAS LEAD-9 SOVEREIGN TRIAD DELIBERATION (LOCAL BARE-METAL FLEET)')
    print(f'Host: Windows Bare Metal | Ollama: {OLLAMA_URL}')
    print('=' * 70)

    turns = []
    for member in COUNCIL_MEMBERS:
        agent = member['agent']
        role = member['role']
        prompt = member['prompt']
        print(f'\n[QUERYING LOCAL MODEL] Calling sovereign-hermes for {agent.upper()} ({role})...')
        try:
            response_text = query_local_ollama('sovereign-hermes', prompt)
        except Exception as err:
            print(f'[Ollama Error on sovereign-hermes]: {err}, falling back to qwen2.5:1.5b')
            response_text = query_local_ollama('qwen2.5:1.5b', prompt)
        
        turns.append({'agent': agent, 'role': role, 'text': response_text})

    print('\n' + '=' * 70)
    print('DISPATCHING DELIBERATION TURNS TO STAGE AND HARDWARE AUDIO')
    print('=' * 70)

    for turn in turns:
        speak_turn(turn['agent'], turn['text'])
        time.sleep(0.6)

    JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    journal_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'live_local_ollama_triad',
        'models_used': ['sovereign-hermes', 'qwen2.5:1.5b'],
        'triad': turns
    }
    with open(JOURNAL_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(journal_entry) + '\n')

    print(f'\n[SUCCESS] Lead-9 Triad Deliberation logged to {JOURNAL_FILE}')

if __name__ == '__main__':
    run_live_triad()
