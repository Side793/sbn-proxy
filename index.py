from flask import Flask, jsonify
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
# Abilita le chiamate cross-origin dalla tua PWA su Netlify
CORS(app) 

@app.route('/api/book/<isbn>', methods=['GET'])
def get_book(isbn):
    try:
        # Chiamata all'API pubblica SRU dell'OPAC SBN forzando il formato Dublin Core
        url = f"https://opac.sbn.it/SRU?operation=searchRetrieve&version=1.1&recordSchema=dc&query=bath.isbn={isbn}"
        
        # Timeout a 8 secondi per evitare che l'app del dottore si blocchi se l'OPAC cade
        response = requests.get(url, timeout=8)
        
        if response.status_code != 200:
            return jsonify({"error": "Errore OPAC SBN"}), 500

        root = ET.fromstring(response.content)
        
        # Gestione dei namespace XML
        ns = {
            'srw': 'http://www.loc.gov/zing/srw/',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        # Verifica se l'ISBN esiste nell'archivio nazionale
        num_records = root.find('.//srw:numberOfRecords', ns)
        if num_records is None or num_records.text == '0':
            return jsonify({"error": "not_found"}), 404

        record = root.find('.//srw:recordData/*', ns)
        
        title = record.find('dc:title', ns)
        author = record.find('dc:creator', ns)
        publisher = record.find('dc:publisher', ns)
        date = record.find('dc:date', ns)

        # Restituisce il JSON identico a quello che si aspetta la tua PWA
        return jsonify({
            "title": title.text if title is not None else "",
            "author": author.text if author is not None else "",
            "publisher": publisher.text if publisher is not None else "",
            "year": date.text if date is not None else "",
            "isbn": isbn
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500