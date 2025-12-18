from flask import Flask, request, jsonify
import sqlite3
import os
import json
from flask_cors import CORS
from main import bot 

app = Flask(__name__)
CORS(app)

DB_FILE = "farm.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS farm_progress (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                hack_level INTEGER DEFAULT 1,
                limit_level INTEGER DEFAULT 0,
                today_mined INTEGER DEFAULT 0,
                mined_date TEXT,
                streak INTEGER DEFAULT 0,
                last_claim TEXT,
                fields_unlocked INTEGER DEFAULT 1,
                reset_data TEXT,
                nickname TEXT DEFAULT 'Игрок'
            )
        ''')

        c.execute("PRAGMA table_info(farm_progress)")
        columns = [col[1] for col in c.fetchall()]

        if 'fields_unlocked' not in columns:
            c.execute("ALTER TABLE farm_progress ADD COLUMN fields_unlocked INTEGER DEFAULT 1")
            print("[INIT] Добавлен столбец fields_unlocked")

        if 'reset_data' not in columns:
            c.execute("ALTER TABLE farm_progress ADD COLUMN reset_data TEXT")
            print("[INIT] Добавлен столбец reset_data")

        if 'nickname' not in columns:
            c.execute("ALTER TABLE farm_progress ADD COLUMN nickname TEXT DEFAULT 'Игрок'")
            print("[INIT] Добавлен столбец nickname")

        conn.commit()
        conn.close()
        print(f"[INIT] Таблица готова. База: {os.path.abspath(DB_FILE)}")
    except Exception as e:
        print(f"[INIT ERROR] Ошибка: {e}")

init_db()

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
            reset_data_str = row[9] if len(row) > 9 else None
            reset_data = json.loads(reset_data_str) if reset_data_str and isinstance(reset_data_str, str) else None

            result = {
                "balance": row[1],
                "hack_level": row[2],
                "limit_level": row[3],
                "today_mined": row[4],
                "mined_date": row[5],
                "streak": row[6],
                "last_claim": row[7],
                "fields_unlocked": row[8] if len(row) > 8 else 1,
                "reset_data": reset_data,
                "nickname": row[10] if len(row) > 10 else 'Игрок'
            }
            return jsonify(result)
        else:
            return jsonify({
                "balance": 0,
                "hack_level": 1,
                "limit_level": 0,
                "today_mined": 0,
                "mined_date": None,
                "streak": 0,
                "last_claim": None,
                "fields_unlocked": 1,
                "reset_data": None,
                "nickname": 'Игрок'
            })

    elif request.method == 'POST':
        data = request.json

        reset_data_raw = data.get('reset_data')
        reset_data_json = json.dumps(reset_data_raw) if reset_data_raw is not None else None

        nickname = data.get('nickname', 'Игрок')
        if len(nickname) > 20:
            nickname = nickname[:20]

        try:
            c.execute('''
                INSERT OR REPLACE INTO farm_progress 
                (user_id, balance, hack_level, limit_level, today_mined, mined_date, streak, last_claim, fields_unlocked, reset_data, nickname)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data.get('balance', 0),
                data.get('hack_level', 1),
                data.get('limit_level', 0),
                data.get('today_mined', 0),
                data.get('mined_date'),
                data.get('streak', 0),
                data.get('last_claim'),
                data.get('fields_unlocked', 1),
                reset_data_json,
                nickname  
            ))
            conn.commit()
            print(f"Прогресс успешно сохранён для user_id={user_id} (ник: {nickname})")
        except Exception as e:
            print(f"ОШИБКА сохранения в БД: {e}")
            conn.rollback()
        finally:
            conn.close()

        return jsonify({"status": "saved"})


@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT nickname, balance 
            FROM farm_progress 
            WHERE balance > 0
            ORDER BY balance DESC 
            LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()

        result = []
        for row in rows:
            nickname = row[0] if row[0] and row[0].strip() else "Игрок"
            balance = row[1] or 0
            result.append({
                "nickname": nickname,
                "balance": balance
            })

        return jsonify(result)
    except Exception as e:
        print(f"[LEADERBOARD ERROR] {e}")
        return jsonify([]), 500

if __name__ == '__main__':
    print("Flask API запущен на порту 10311 — с лидербордом и никнеймами ♡")
    app.run(host='0.0.0.0', port=10311)