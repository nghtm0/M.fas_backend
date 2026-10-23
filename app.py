from flask import Flask, request, jsonify
import psycopg2
import os
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# QUI METTERAI LA STRINGA DI CONNESSIONE DI NEON (Gestionale o Layer IA)
# Usa la stringa di moncler-ai-layer per ora, poi vediamo.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_bLlyD3NHoVa5@ep-calm-dawn-b41p54cm-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

@app.route('/query', methods=['POST'])
def esegui_query():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Nessuna query fornita"}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            result = cur.fetchall()
            conn.close()
            return jsonify({"status": "success", "data": result})
        else:
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "message": "Query eseguita"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)