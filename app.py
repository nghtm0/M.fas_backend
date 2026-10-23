from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import requests
import json

app = Flask(__name__)

# Usa la stringa di connessione di Neon (Layer IA o Gestionale)
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

@app.route('/predict_trend', methods=['POST'])
def predict_trend():
    data = request.json
    product_name = data.get('product_name', 'Giacca Maya')
    
    # 1. Prendiamo i dati dal DB
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT SUM(quantity) as total_sold 
            FROM transactions t
            JOIN products p ON t.product_id = p.product_id
            WHERE p.product_name ILIKE %s 
            AND t.transaction_date >= NOW() - INTERVAL '30 days'
        """, (f'%{product_name}%',))
        sales_data = cur.fetchone()
        conn.close()
        vendite = sales_data['total_sold'] if sales_data and sales_data['total_sold'] else 0
    except Exception as e:
        return jsonify({"error": f"Errore DB: {str(e)}"}), 500

    # 2. Chiamiamo l'API di Fastweb
    # SOSTITUISCI QUESTA STRINGA CON LA TUA CHIAVE REALE
    fastweb_api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InBqaEZoNnA5UDRnQVVIaEFDZHdDQW1GMFY1Z0VuSXBvV0FOOUhrTmRkd1k9In0.eyJpc3MiOiJodHRwczovL2FpLWZhY3RvcnkuZmFzdHdlYi5pdCIsInN1YiI6ImhhY2thdGhvbiIsInRlbmFudCI6InN1cGVycG9kIiwibmFtZXNwYWNlIjoiY29lLXZsbG0tcXdlbi0zOTdiIiwiaWF0IjoxNzkxOTgyNTIyLCJleHAiOjE3OTI4ODY0MDB9.Ut9JKXi2T18fDCv3zJA9oJlJSjE-WuMRblD7IHTBruhBH8X5vuip2WwFLN9ViDwwKAIzXZnZMBSgXa0Dg85my7GeCJT7fEr7M1lb-K0iAxKjHY7jeXZz_cTYzXjLyWjJu_Zs_DeG3Uvwyi5bEAzcfJ_11fk49jaiv_3zWGmGFniAERQHD5U7iC6AI7qtH_Bux6Z7pcmQ9VXdI22ZmEh14fTqpJH9jgw5EyD6y28JeQhT5QyLGofK4jLpGJr_l9t3aRSiencEedA8FYBRnfI8OptfG6DXW7BeLLrUJOjxC0LLdxeBWOmfXAxoRxqHv7XF6EYEh13duNwphH8PcFL-eQ" 
    
   

    headers = {
        "Authorization": f"Bearer {fastweb_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Sei un analista di trend per Moncler. 
    Il prodotto '{product_name}' ha venduto {vendite} pezzi negli ultimi 30 giorni.
    Basandoti su questo, dammi una previsione per le prossime 2 settimane.
    Rispondi SOLO in formato JSON con le chiavi: "trend_score" (0-100), "direction" ("Rising", "Stable", "Falling") e "reasoning" (breve spiegazione)."""
    
    payload = {
        "model": "Qwen/Qwen3.5-397B-A17B-FP8",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    try:
        response = requests.post("https://spod.ai-factory.fastweb.it/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        risultato = response.json()['choices'][0]['message']['content']
        return jsonify({"status": "success", "trend_analysis": risultato})
    except Exception as e:
        return jsonify({"error": f"Errore Fastweb: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
