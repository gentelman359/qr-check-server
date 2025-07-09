from flask import Flask, request, render_template_string
from datetime import datetime, timedelta
import json, os, hashlib

app = Flask(__name__)

CONFIG_FILE_PATH = "kiosk_config.json"
QR_SECRET_KEY = "wedding_secret_key_1234"  # 🚨 반드시 kiosk와 동일하게 설정

used_qr = set()

def load_used_qr():
    return used_qr

def save_used_qr(qr_set):
    global used_qr
    used_qr = qr_set

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

    # ✅ 파라미터 누락
    if not token or not issue_time_str:
        return error_html("❌ 인증 파라미터 누락")

    # ✅ 설정 파일 없음
    if not os.path.exists(CONFIG_FILE_PATH):
        return error_html("❌ 설정 파일이 없습니다.")

    # ✅ 설정 로딩
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config_info = json.load(f)
    except Exception as e:
        return error_html(f"❌ 설정 파일 로딩 실패: {e}")

    # ✅ 시간 파싱
    try:
        wedding_dt = datetime.strptime(f"{config_info['date']} {config_info['hour']}:{config_info['minute']}", "%Y-%m-%d %H:%M")
    except Exception as e:
        return error_html(f"❌ 예식 시간 파싱 실패: {e}")

    now = datetime.now()

    # ✅ 시간 유효성 확인
    if not (wedding_dt - timedelta(hours=1) <= now <= wedding_dt + timedelta(hours=2)):
        return error_html("❌ 유효 시간 초과입니다.")

    # ✅ 토큰 검증
    if not is_token_valid(serial, issue_time_str, token):
        return error_html("❌ 토큰이 유효하지 않습니다.")

    # ✅ 이미 사용된 QR 확인
    used = load_used_qr()
    if serial in used:
        return error_html("❌ 이미 사용된 QR입니다.")

    # ✅ 정상 처리
    used.add(serial)
    save_used_qr(used)
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
