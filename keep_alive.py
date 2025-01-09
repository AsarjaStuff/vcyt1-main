import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    # Redirect to a page to keep the app alive
    return '<meta http-equiv="refresh" content="0; URL=https://phantom.fr.to/support"/>'

def run():
    # Use the PORT environment variable if it's defined; otherwise, default to 8080.
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run)
    server.start()
