from flask import Flask, render_template_string
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# ✅ 설정 파일 경로 (main.py에서 저장하는 JSON 경로와 동일해야 함)
CONFIG_FILE_PATH = "kiosk_config.json"

# ✅ 사용된 QR코드 추적용 (메모리상 집합)
used_qr = set()

# ✅ 사용된 QR 저장/불러오기 함수 (선택: 파일로 저장하려면 수정 가능)
def load_used_qr():
    return used_qr

def save_used_qr(qr_set):
    global used_qr
    used_qr = qr_set

# ✅ QR 인증 라우트
@app.route("/q/<serial>")
def validate_qr(serial):
    # 설정 파일이 없다면 기본 에러 표시
    if not os.path.exists(CONFIG_FILE_PATH):
        return error_html("❌ 설정 파일이 없습니다.")

    # 설정 파일 로딩
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
        config_info = json.load(f)

    # 예식 시간 구성
    try:
        wedding_dt = datetime.strptime(
            f"{config_info['date']} {config_info['hour']}:{config_info['minute']}",
            "%Y-%m-%d %H:%M"
        )
    except Exception as e:
        return error_html(f"❌ 예식 시간 파싱 실패: {e}")

    now = datetime.now()

    # ✅ 유효 시간 초과
    if not (wedding_dt - timedelta(hours=1) <= now <= wedding_dt + timedelta(hours=2)):
        return error_html("❌ 유효 시간 초과입니다.")

    # ✅ 이미 사용된 QR
    used = load_used_qr()
    if serial in used:
        return error_html("❌ 이미 사용된 QR입니다.")

    # ✅ 정상 입장 처리
    used.add(serial)
    save_used_qr(used)
    return success_html("✅ 입장 허용")

# ✅ 성공/에러 화면 공통 HTML
def error_html(message):
    return render_template_string(f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script>
            setTimeout(function() {{
                window.close();
            }}, 2000);
        </script>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-size: 3em;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div style="color:red;">{message}</div>
    </body>
    </html>
    """)

def success_html(message):
    return render_template_string(f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script>
            setTimeout(function() {{
                window.close();
            }}, 2000);
        </script>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                font-size: 3em;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div style="color:green;">{message}</div>
    </body>
    </html>
    """)

# ✅ 서버 실행
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)