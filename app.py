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
    import requests

@app.route('/predict_trend', methods=['POST'])
def predict_trend():
    data = request.json
    product_name = data.get('product_name')
    
    # 1. Prendiamo i dati storici dal nostro DB (es. vendite ultimi 30 giorni)
    # (Qui usiamo la tua connessione a Neon esistente)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT SUM(quantity) as total_sold 
        FROM transactions t
        JOIN products p ON t.product_id = p.product_id
        WHERE p.product_name LIKE %s 
        AND t.transaction_date >= NOW() - INTERVAL '30 days'
    """, (f'%{product_name}%',))
    sales_data = cur.fetchone()
    conn.close()

    # 2. Chiamiamo l'API di Fastweb (Qwen)
    fastweb_api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InBqaEZoNnA5UDRnQVVIaEFDZHdDQW1GMFY1Z0VuSXBvV0FOOUhrTmRkd1k9In0.eyJpc3MiOiJodHRwczovL2FpLWZhY3RvcnkuZmFzdHdlYi5pdCIsInN1YiI6ImhhY2thdGhvbiIsInRlbmFudCI6InN1cGVycG9kIiwibmFtZXNwYWNlIjoiY29lLXZsbG0tcXdlbi0zOTdiIiwiaWF0IjoxNzkxOTgyNTIyLCJleHAiOjE3OTI4ODY0MDB9.Ut9JKXi2T18fDCv3zJA9oJlJSjE-WuMRblD7IHTBruhBH8X5vuip2WwFLN9ViDwwKAIzXZnZMBSgXa0Dg85my7GeCJT7fEr7M1lb-K0iAxKjHY7jeXZz_cTYzXjLyWjJu_Zs_DeG3Uvwyi5bEAzcfJ_11fk49jaiv_3zWGmGFniAERQHD5U7iC6AI7qtH_Bux6Z7pcmQ9VXdI22ZmEh14fTqpJH9jgw5EyD6y28JeQhT5QyLGofK4jLpGJr_l9t3aRSiencEedA8FYBRnfI8OptfG6DXW7BeLLrUJOjxC0LLdxeBWOmfXAxoRxqHv7XF6EYEh13duNwphH8PcFL-eQ"
    headers = {
        "Authorization": f"Bearer {fastweb_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Sei un analista di trend per Moncler. 
    Il prodotto '{product_name}' ha venduto {sales_data['total_sold'] or 0} pezzi negli ultimi 30 giorni.
    Basandoti su questa informazione e sul fatto che siamo in inverno (stagionalità), 
    dammi una previsione di trend per le prossime 2 settimane. 
    Rispondi in formato JSON con: 'trend_score' (0-100), 'direction' ('Rising', 'Stable', 'Falling') e 'reasoning' (1 frase).
    """
    
    payload = {
        "model": "Qwen/Qwen3.5-397B-A17B-FP8",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    response = requests.post("https://spod.ai-factory.fastweb.it/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        return jsonify(response.json()['choices'][0]['message']['content'])
    else:
        return jsonify({"error": "Errore API Fastweb"}), 500
