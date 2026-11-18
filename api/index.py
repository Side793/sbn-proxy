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
    
    # Motore 1: OPAC SBN Mobile Gateway
    try:
        url_sbn = f"http://opac.sbn.it/opacmobilegw/search.json?isbn={isbn}"
        res_sbn = requests.get(url_sbn, headers=headers, timeout=5)
        if res_sbn.status_code == 200:
            data = res_sbn.json()
            # SBN restituisce un dizionario con la chiave 'briefRecords' che contiene la lista dei risultati
            records = data.get('briefRecords', []) if isinstance(data, dict) else data
            if isinstance(records, list) and len(records) > 0:
                book = records[0]
                return jsonify({
                    "title": book.get("titolo", ""),
                    "author": book.get("autorePrincipale", ""),
                    "publisher": book.get("pubblicazione", ""),
                    "year": book.get("annoPubblicazione", ""),
                    "isbn": isbn
                })
    except Exception as e:
        print(f"Errore SBN: {e}")

    # Motore 2: Fallback Google Books API
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
    except Exception as e:
        print(f"Errore Google Books: {e}")

    return jsonify({"error": "not_found"}), 404
