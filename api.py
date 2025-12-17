from flask import Flask, request, jsonify
import sqlite3
from main import bot 

app = Flask(__name__)
DB_FILE = "farm.db"

@app.route('/api/farm', methods=['GET', 'POST'])
def farm_api():
    user_id = request.args.get('user_id') if request.method == 'GET' else request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == 'GET':
        c.execute("SELECT * FROM farm_progress WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return jsonify({
                "balance": row[1],
                "hack_level": row[2],
                "limit_level": row[3],
                "today_mined": row[4],
                "mined_date": row[5],
                "streak": row[6],
                "last_claim": row[7]
            })
        return jsonify({"balance": 0, "hack_level": 1, "limit_level": 0})

    elif request.method == 'POST':
        data = request.json
        c.execute('''
            INSERT OR REPLACE INTO farm_progress 
            (user_id, balance, hack_level, limit_level, today_mined, mined_date, streak, last_claim)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('balance', 0),
            data.get('hack_level', 1),
            data.get('limit_level', 0),
            data.get('today_mined', 0),
            data.get('mined_date'),
            data.get('streak', 0),
            data.get('last_claim')
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "saved"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10311)