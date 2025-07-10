from flask import Flask, render_template_string, request
from datetime import datetime, timedelta
import pytz
import json
import os
import re
import hashlib 
app = Flask(__name__)
CONFIG_FILE_PATH = "kiosk_config.json"
QR_SECRET_KEY = "wedding_secret_key_1234"  # 🚨 반드시 kiosk와 동일하게 설정
used_qr = set()
korea = pytz.timezone("Asia/Seoul")


def load_used_qr(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data)

def save_used_qr(qr_set, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(list(qr_set), f)
def get_used_qr_filename(date, hour, minute, groom, bride):
    key = f"{date}_{hour}_{minute}_{groom}_{bride}"
    safe_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
    return f"used_qr_{safe_key}.json"
# ✅ 토큰 생성 / 검증
def generate_secure_token(serial, issue_time_str):
    data = f"{serial}|{issue_time_str}|{QR_SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()

def is_token_valid(serial, issue_time_str, token):
    expected = generate_secure_token(serial, issue_time_str)
    return token == expected

@app.route("/q/<serial>")
def validate_qr(serial):
    token = request.args.get("t", "")
    issue_time_str = request.args.get("ts", "")
    now = datetime.now(korea)  # 한국시간으로 현재 시간 받아오기
    # 예식 관련 파라미터
    date = request.args.get("date", "")
    hour = request.args.get("hour", "")
    minute = request.args.get("minute", "")

    # 필수 파라미터 체크
    if not (token and issue_time_str and date and hour and minute):
        return error_html("❌ 필수 인증 및 예식 파라미터 누락")

    # 예식 시간 파싱
    try:
        wedding_dt = datetime.strptime(f"{date} {hour}:{minute}", "%Y-%m-%d %H:%M")
    except Exception as e:
        return error_html(f"❌ 예식 시간 파싱 실패: {e}")

    now = datetime.now()

    # 유효 시간 검사
    if not (wedding_dt - timedelta(hours=1) <= now <= wedding_dt + timedelta(hours=2)):
        return error_html("❌ 유효 시간 초과입니다.")

    # 토큰 검증
    if not is_token_valid(serial, issue_time_str, token):
        return error_html("❌ 토큰이 유효하지 않습니다.")

    # used_qr 파일명 생성
    used_qr_filename = get_used_qr_filename(date, hour, minute)

    # 이미 사용된 QR 체크
    used = load_used_qr(used_qr_filename)
    if serial in used:
        return error_html("❌ 이미 사용된 QR입니다.")

    # 정상 처리
    used.add(serial)
    save_used_qr(used, used_qr_filename)
    return success_html("✅ 입장 허용")

# ✅ 공통 UI
def error_html(message):
    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>setTimeout(() => window.close(), 2000);</script>
    <style>body {{ display: flex; justify-content: center; align-items: center; height: 100vh; font-size: 3em; font-weight: bold; }}</style>
    </head><body><div style="color:red;">{message}</div></body></html>
    """)

def success_html(message):
    return render_template_string(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>setTimeout(() => window.close(), 2000);</script>
    <style>body {{ display: flex; justify-content: center; align-items: center; height: 100vh; font-size: 3em; font-weight: bold; }}</style>
    </head><body><div style="color:green;">{message}</div></body></html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
