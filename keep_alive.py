import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    # Replace the URL below with any URL you want to redirect to.
    return '<meta http-equiv="refresh" content="0; URL=https://www.google.com"/>'

def run():
    # Use the PORT environment variable if it's defined; otherwise, default to 8080.
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run)
    server.start()
