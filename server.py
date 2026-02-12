from flask import Flask, redirect, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_url(code):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM links WHERE code=?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def register_click(code):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE links SET clicks = clicks + 1 WHERE code=?", (code,))
    cursor.execute("INSERT INTO clicks VALUES (?, ?, ?, ?)",
                   (code,
                    datetime.now().isoformat(),
                    request.remote_addr,
                    request.headers.get("User-Agent")))
    conn.commit()
    conn.close()

@app.route('/<code>')
def redirect_to_url(code):
    url = get_url(code)
    if url:
        register_click(code)
        return redirect(url, code=302)
    return "404", 404

if __name__ == "__main__":
    app.run(port=5000)