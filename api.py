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
                reset_data TEXT
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

        conn.commit()
        conn.close()
        print(f"[INIT] Таблица готова. База: {os.path.abspath(DB_FILE)}")
    except Exception as e:
        print(f"[INIT ERROR] Ошибка: {e}")

init_db()

@app.route('/api/farm', methods=['GET', 'POST'])
def farm_api():
    print(f"\n=== Новый запрос {request.method} от {request.remote_addr} ===")
    if request.method == 'POST':
        print(f"JSON данные: {request.get_json()}")
    else:
        print(f"Параметры: {request.args}")

    user_id = request.args.get('user_id') if request.method == 'GET' else request.json.get('user_id')
    if not user_id:
        print("ОШИБКА: user_id не передан")
        return jsonify({"error": "user_id required"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == 'GET':
        print(f"GET запрос для user_id={user_id}")
        c.execute("SELECT * FROM farm_progress WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            reset_data_str = row[9] if len(row) > 9 else None
            if reset_data_str is not None and isinstance(reset_data_str, str):
                try:
                    reset_data = json.loads(reset_data_str)
                except json.JSONDecodeError:
                    reset_data = None
            else:
                reset_data = None
            
            result = {
                "balance": row[1],
                "hack_level": row[2],
                "limit_level": row[3],
                "today_mined": row[4],
                "mined_date": row[5],
                "streak": row[6],
                "last_claim": row[7],
                "fields_unlocked": row[8] if len(row) > 8 else 1,
                "reset_data": reset_data
            }
            print(f"Найден прогресс: {result}")
            return jsonify(result)
        else:
            print(f"Прогресс не найден — возвращаем дефолт")
            return jsonify({
                "balance": 0,
                "hack_level": 1,
                "limit_level": 0,
                "today_mined": 0,
                "mined_date": None,
                "streak": 0,
                "last_claim": None,
                "fields_unlocked": 1,
                "reset_data": None
            })

    elif request.method == 'POST':
        data = request.json


        reset_data_raw = data.get('reset_data')
        reset_data_json = json.dumps(reset_data_raw) if reset_data_raw is not None else None

        try:
            c.execute('''
                INSERT OR REPLACE INTO farm_progress 
                (user_id, balance, hack_level, limit_level, today_mined, mined_date, streak, last_claim, fields_unlocked, reset_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                reset_data_json
            ))
            conn.commit()
            print(f"Прогресс успешно сохранён для user_id={user_id}")
        except Exception as e:
            print(f"ОШИБКА сохранения в БД: {e}")
            conn.rollback()
        finally:
            conn.close()

        return jsonify({"status": "saved"})

if __name__ == '__main__':
    print("Flask API запущен на порту 10311 с поддержкой CORS и безопасным JSON")
    app.run(host='0.0.0.0', port=10311)