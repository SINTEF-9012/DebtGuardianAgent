import subprocess
import signal
import os
import time
import threading
import ollama
from typing import Optional

# --- Ollama Query Function ---

def warm_model(model: str, retries: int = 3, delay: float = 2.0) -> bool:
    """
    Pre-load a model in the Ollama server so the first real request
    does not hit a cold-start 500.  Sends a minimal generate call and
    retries on failure (the server may need a second attempt with its
    fallback runner engine).

    Returns True if the model responded, False otherwise.
    """
    for attempt in range(1, retries + 1):
        try:
            ollama.generate(model=model, prompt="hi", options={"num_predict": 1})
            print(f"[Ollama] Model '{model}' warmed up (attempt {attempt})")
            return True
        except Exception as e:
            print(f"[Ollama] Warm-up attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    print(f"[Ollama] WARNING: Could not pre-load model '{model}'")
    return False


def ask_ollama(model, prompt, temperature=0):
    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={'temperature': temperature,
                     'num_ctx':262144},
            think = False
        )
    except ollama.ResponseError as e:
        print('Error:', e.error)
        return None
    return response.get('response', None)

def is_ollama_running() -> bool:
    """Check if the Ollama server is currently running and reachable."""
    try:
        client = ollama.Client()
        client.list()  # lightweight API call, returns installed models
        return True
    except Exception:
        return False
    
def _start_ollama_server_base(
    stream_stdout: bool = False,
    log_file: Optional[str] = None
) -> subprocess.Popen:
    """
    Helper to start the Ollama server with optional stdout streaming or logging.
    """
    print("Starting Ollama server...")
    if log_file:
        logfile = open(log_file, "w")
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=logfile,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        return process
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid
    )
    if stream_stdout:
        def stream_output(stream, prefix):
            for line in iter(stream.readline, ''):
                print(f"[{prefix}] {line}", end='')
        threading.Thread(target=stream_output, args=(process.stdout, 'STDOUT'), daemon=True).start()
        threading.Thread(target=stream_output, args=(process.stderr, 'STDERR'), daemon=True).start()
    return process

def start_ollama_server() -> subprocess.Popen:
    """Start Ollama server (no output streaming)."""
    return _start_ollama_server_base()

def start_ollama_server_stream_stdout() -> subprocess.Popen:
    """Start Ollama server and stream stdout/stderr to console."""
    return _start_ollama_server_base(stream_stdout=True)

def start_ollama_server_log(log_file: str = "ollama.log") -> subprocess.Popen:
    """Start Ollama server and log output to a file."""
    return _start_ollama_server_base(log_file=log_file)

def stop_ollama_server(process: subprocess.Popen) -> None:
    """Stop the Ollama server process."""
    print("Stopping Ollama server...")
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except Exception as e:
        print(f"Error stopping Ollama server: {e}")
