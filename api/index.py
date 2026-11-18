from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app) 

@app.route('/api/book/<isbn>', methods=['GET'])
def get_book(isbn):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Motore 1: OPAC SBN Mobile Gateway (Dati ministeriali italiani in JSON)
    try:
        url_sbn = f"http://opac.sbn.it/opacmobilegw/search.json?isbn={isbn}"
        res_sbn = requests.get(url_sbn, headers=headers, timeout=5)
        if res_sbn.status_code == 200:
            data = res_sbn.json()
            if isinstance(data, list) and len(data) > 0:
                book = data[0]
                return jsonify({
                    "title": book.get("titolo", ""),
                    "author": book.get("autorePrincipale", ""),
                    "publisher": book.get("pubblicazione", ""),
                    "year": book.get("annoPubblicazione", ""),
                    "isbn": isbn
                })
    except Exception:
        pass

    # Motore 2: Fallback Google Books API (Intervento di emergenza se SBN fallisce)
    try:
        url_gb = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        res_gb = requests.get(url_gb, timeout=5)
        if res_gb.status_code == 200:
            data = res_gb.json()
            if data.get("totalItems", 0) > 0:
                info = data["items"][0].get("volumeInfo", {})
                return jsonify({
                    "title": info.get("title", ""),
                    "author": ", ".join(info.get("authors", [])),
                    "publisher": info.get("publisher", ""),
                    "year": info.get("publishedDate", "")[:4] if info.get("publishedDate") else "",
                    "isbn": isbn
                })
    except Exception:
        pass

    return jsonify({"error": "not_found"}), 404
