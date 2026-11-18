from flask import Flask, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

YEAR_RE = re.compile(r'(?<!\d)(1[4-9]\d{2}|20\d{2})(?!\d)')


def extract_year(*values):
    for val in values:
        if not val:
            continue
        match = YEAR_RE.search(str(val))
        if match:
            return match.group(1)
    return ""


def clean_sbn_title(raw_title):
    if not raw_title:
        return ""
    # Elimina la formulazione di responsabilità ISBD (" / Autore ; illustrazioni...")
    title = raw_title.split(" / ", 1)[0]
    # Rimuove prefissi numerici o di collana tra parentesi quadre (es. "[1]: ")
    title = re.sub(r'^\s*\[[^\]]+\]\s*:\s*', '', title)
    # Rimuove gli asterischi di non-ordinamento SBN (es. "*Nome della rosa")
    title = title.replace('*', '')
    return re.sub(r'\s+', ' ', title).strip(" /:;,")


def clean_sbn_author(raw_author):
    if not raw_author:
        return ""
    # Rimuove qualificazioni d'autorità tra parentesi angolari (es. "<1975->")
    author = re.sub(r'\s*<[^>]*>', '', raw_author).strip()
    # Uniforma "Cognome, Nome" -> "Nome Cognome" per coerenza con Google Books
    if author.count(',') == 1 and ':' not in author and ';' not in author:
        cognome, nome = [part.strip() for part in author.split(',', 1)]
        if cognome and nome:
            author = f"{nome} {cognome}"
    return re.sub(r'\s+', ' ', author).strip()


def clean_sbn_publisher(raw_pub):
    if not raw_pub:
        return ""
    pub = str(raw_pub)
    # Formato ISBD "Luogo : Editore, Anno" -> isola la parte successiva ai due punti
    if ':' in pub:
        pub = pub.split(':', 1)[1]
    # Rimuove la coda con data, copyright, stampa o "s.d."
    pub = re.sub(
        r',\s*(?:(?:c\.?|cop\.?|©\s*|stampa\s+)?\[?(?:\d{4}|s\.d\.|s\.a\.)).*$',
        '',
        pub,
        flags=re.IGNORECASE,
    )
    pub = pub.strip(" [].,;:")
    if pub.lower() in ('s.n.', 's.n', 'sine nomine'):
        return ""
    return re.sub(r'\s+', ' ', pub).strip()


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
            records = data.get('briefRecords', []) if isinstance(data, dict) else data
            if isinstance(records, list) and len(records) > 0:
                book = records[0]
                raw_pub = book.get("pubblicazione", "")
                title = clean_sbn_title(book.get("titolo", ""))
                if title:
                    return jsonify({
                        "title": title,
                        "author": clean_sbn_author(book.get("autorePrincipale", "")),
                        "publisher": clean_sbn_publisher(raw_pub),
                        "year": extract_year(book.get("annoPubblicazione"), raw_pub),
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
                title = (info.get("title") or "").strip()
                subtitle = (info.get("subtitle") or "").strip()
                full_title = f"{title}: {subtitle}" if (title and subtitle) else title
                if full_title:
                    return jsonify({
                        "title": full_title,
                        "author": ", ".join(info.get("authors", [])),
                        "publisher": (info.get("publisher") or "").strip(),
                        "year": extract_year(info.get("publishedDate")),
                        "isbn": isbn
                    })
    except Exception as e:
        print(f"Errore Google Books: {e}")

    return jsonify({"error": "not_found"}), 404
