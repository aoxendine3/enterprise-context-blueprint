import json
import time

_initialized = False
_data = []
_latency = 0.005  # 5ms
_force_error = False


def initialize_db():
    global _initialized, _data, _force_error
    if _force_error:
        raise RuntimeError("Forced DB Error")
    _initialized = True
    _data = []


def reset_db():
    initialize_db()


def set_latency(latency_seconds: float):
    global _latency
    _latency = latency_seconds


def set_force_error(force: bool):
    global _force_error
    _force_error = force


def migrate_json_data(memory_path: str = "Source/xoras_memory.json", knowledge_path: str = "Source/XORAS_ACTIVE_KNOWLEDGE.json"):
    global _initialized, _data
    if not _initialized:
        raise RuntimeError("Database not initialized")
    if _force_error:
        raise RuntimeError("Forced DB Error")

    # Read memory_path
    try:
        with open(memory_path, 'r') as f:
            mem_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValueError(f"Failed to migrate memory JSON: {str(e)}")

    # Read knowledge_path
    try:
        with open(knowledge_path, 'r') as f:
            kn_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        raise ValueError(f"Failed to migrate knowledge JSON: {str(e)}")

    # Standardize data format into _data
    if isinstance(mem_data, list):
        for item in mem_data:
            text = item.get('text', '')
            if not any(d.get('text') == text for d in _data):
                _data.append(item)
    elif isinstance(mem_data, dict):
        for k, v in mem_data.items():
            if not any(d.get('text') == str(v) for d in _data):
                _data.append({'text': str(v), 'domain': k})

    if isinstance(kn_data, dict):
        for key, value in kn_data.items():
            if isinstance(value, list):
                for subitem in value:
                    text_repr = json.dumps(subitem)
                    if not any(d.get('text') == text_repr for d in _data):
                        _data.append({'text': text_repr, 'domain': key})
            else:
                text_repr = json.dumps(value)
                if not any(d.get('text') == text_repr for d in _data):
                    _data.append({'text': text_repr, 'domain': key})


def query_semantic_memory(query: str, limit: int = 10):
    global _initialized, _data, _latency, _force_error
    if not _initialized:
        raise RuntimeError("Database not initialized")
    if _force_error:
        raise RuntimeError("Forced DB Error")

    if not query or not query.strip():
        return []

    if _latency > 0:
        time.sleep(_latency)

    matches = []
    query_lower = query.lower()

    for item in _data:
        text = item.get('text', '').lower()
        domain = item.get('domain', '').lower()
        score = 0
        for word in query_lower.split():
            if word in text:
                score += 2
            if word in domain:
                score += 5
        if score > 0 or not query_lower.strip():
            matches.append((score, item))

    matches.sort(key=lambda x: x[0], reverse=True)
    results = [item for score, item in matches[:limit]]

    if not results and _data:
        results = _data[:limit]

    return results
