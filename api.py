from flask import Flask, request, jsonify
import sqlite3
import os
import json
from datetime import datetime
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
                miner_level INTEGER DEFAULT 0,
                last_miner_claim INTEGER DEFAULT 0
            )
        ''')

        c.execute("PRAGMA table_info(farm_progress)")
        columns = [col[1] for col in c.fetchall()]

        if 'fields_unlocked' not in columns:
            c.execute("ALTER TABLE farm_progress ADD COLUMN fields_unlocked INTEGER DEFAULT 1")

        if 'reset_data' not in columns:
            c.execute("ALTER TABLE farm_progress ADD COLUMN reset_data TEXT")

        if 'miner_level' not in columns:
            c.execute("ALTER TABLE farm_progress ADD COLUMN miner_level INTEGER DEFAULT 0")

        if 'last_miner_claim' not in columns:
            c.execute("ALTER TABLE farm_progress ADD COLUMN last_miner_claim INTEGER DEFAULT 0")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[INIT ERROR] Ошибка инициализации БД: {e}")

init_db()

@app.route('/api/farm', methods=['GET', 'POST'])
def farm_api():
    user_id = None

    if request.method == 'GET':
        user_id = request.args.get('user_id')
    elif request.method == 'POST':
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id') or data.get('user484_id')

    if not user_id:
        app.logger.error("ОШИБКА: user_id не передан")
        return jsonify({"error": "user_id required"}), 400

    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "user_id должен быть числом"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == 'GET':
        c.execute("SELECT * FROM farm_progress WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()

        if row:
            reset_data = None
            if row[9]:
                try:
                    reset_data = json.loads(row[9])
                except:
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
                "reset_data": reset_data,
                "miner_level": row[10] if len(row) > 10 else 0,
                "last_miner_claim": row[11] if len(row) > 11 else int(datetime.now().timestamp() * 1000)
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
                "miner_level": 0,
                "last_miner_claim": int(datetime.now().timestamp() * 1000)
            })

    elif request.method == 'POST':
        data = request.get_json(silent=True) or {}

        reset_data_json = None
        reset_data_raw = data.get('reset_data')
        if reset_data_raw is not None:
            try:
                reset_data_json = json.dumps(reset_data_raw)
            except:
                reset_data_json = None

        def safe_int(value, default=0):
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default

        balance = safe_int(data.get('balance'), 0)
        hack_level = safe_int(data.get('hack_level'), 1)
        limit_level = safe_int(data.get('limit_level'), 0)
        today_mined = safe_int(data.get('today_mined'), 0)
        streak = safe_int(data.get('streak'), 0)
        fields_unlocked = safe_int(data.get('fields_unlocked'), 1)
        miner_level = safe_int(data.get('miner_level'), 0)
        last_miner_claim = safe_int(data.get('last_miner_claim'), int(datetime.now().timestamp() * 1000))

        try:
            c.execute('''
                INSERT OR REPLACE INTO farm_progress 
                (user_id, balance, hack_level, limit_level, today_mined, mined_date, streak, last_claim, fields_unlocked, reset_data, miner_level, last_miner_claim)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                balance,
                hack_level,
                limit_level,
                today_mined,
                data.get('mined_date'),
                streak,
                data.get('last_claim'),
                fields_unlocked,
                reset_data_json,
                miner_level,
                last_miner_claim
            ))
            conn.commit()
            app.logger.info(f"Прогресс успешно сохранён для user_id={user_id}")
        except Exception as e:
            app.logger.error(f"ОШИБКА сохранения в БД: {e}")
            conn.rollback()
        finally:
            conn.close()

        return jsonify({"status": "saved"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10311)