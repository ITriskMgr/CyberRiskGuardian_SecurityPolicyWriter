"""Start the Policy Builder on this computer only (127.0.0.1). Usage: python3 serve.py [port]"""
import os
import sys
import webbrowser
from threading import Timer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PB_PORT", "8120"))
    from app import config
    import uvicorn
    host = config.settings.host
    url = f"http://localhost:{port}/"
    print(f"\n  {config.APP_NAME} {config.APP_VERSION}\n  Open {url}  (Control-C to stop)\n  Data folder: {config.settings.data_dir}\n"
          f"  AI provider: {'Claude (' + config.settings.ai_model + ')' if config.settings.ai_available else 'offline / deterministic'}\n")
    if os.environ.get("PB_NO_BROWSER") != "1":
        Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run("app.main:app", host=host, port=port, log_level="warning")
