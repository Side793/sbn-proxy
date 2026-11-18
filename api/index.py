from flask import Flask, jsonify
from flask_cors import CORS
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app) 

@app.route('/api/book/<isbn>', methods=['GET'])
def get_book(isbn):
    try:
        url = f"https://opac.sbn.it/SRU?operation=searchRetrieve&version=1.1&recordSchema=dc&query=bath.isbn={isbn}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code != 200:
            return jsonify({
                "error": "Blocco Server SBN",
                "status_code": response.status_code,
                "dettaglio_risposta": response.text[:200]
            }), 500

        root = ET.fromstring(response.content)
        
        ns = {
            'srw': 'http://www.loc.gov/zing/srw/',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        num_records = root.find('.//srw:numberOfRecords', ns)
        if num_records is None or num_records.text == '0':
            return jsonify({"error": "not_found"}), 404

        record = root.find('.//srw:recordData/*', ns)
        
        title = record.find('dc:title', ns)
        author = record.find('dc:creator', ns)
        publisher = record.find('dc:publisher', ns)
        date = record.find('dc:date', ns)

        return jsonify({
            "title": title.text if title is not None else "",
            "author": author.text if author is not None else "",
            "publisher": publisher.text if publisher is not None else "",
            "year": date.text if date is not None else "",
            "isbn": isbn
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
