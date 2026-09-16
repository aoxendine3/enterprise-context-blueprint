import urllib
import json

# MODEL_REGistry: model name -> capability list
MODEL_REGistry = {
    'sovereign-hermes': ['reasoning', 'code_generation', 'planning', 'orchestration'],
    'deepseek-r1.5b': ['verification', 'linting', 'status_checks', 'quick_commands'],
    'hermes3.8b': ['fallback_reasoning', 'code_review'],
    'qwen-2.5.1': ['summarization', 'lightweight_queries'],
    'llama3.2': ['general_chat', 'bracketing']
}

def select_model(intent):
    """Select the best model based on the intent."""
    selected_model = None
    for model_name, capabilities in MODEL_REGistry.items():
        if intent in capabilities:
            selected_model = model_name
            return selected_model
    return None

def dispatch(model_name, prompt):
    """Dispatch the prompt to Ollama and return the URL."""
    import urllib
    import json
    import time

    try:
        response = json.loads(urlparse(f'http://127.0.0.1:11434/api/generate?model={model_name}&prompt={prompt}').query)
        return f'http://127.0.0.1:11434/api/generate?model={model_name}&prompt={prompt}'
    except json.JSONDecodeError:
        time.sleep(1)
        return dispatch(model_name, prompt)

def orchestrate(transcript):
    """Orbit model to process the transcript and return the result."""
    import urllib
    import json
    import time

    transcript_tokens = transcript.split()
    model = select_model(transcript_tokens[0])