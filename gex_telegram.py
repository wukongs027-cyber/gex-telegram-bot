import requests
from datetime import datetime
import pytz
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code == 200:
            print("✅ 发送成功")
            return True
        else:
            print(f"❌ 发送失败: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False

def get_gex(ticker: str) -> dict:
    url = f"https://algoxflow.com/api/gexmap?ticker={ticker}"
    try:
        data = requests.get(url, timeout=10).json()
        return {
            "spot": data.get("spot"),
            "net_gex": data.get("totalGex"),
            "flip": data.get("flip"),
            "call_wall": data.get("callWall"),
            "put_wall": data.get("putWall"),
            "regime": data.get("regime", "unknown")
        }
    except Exception as e:
        return {"error": str(e)}

def build_message() -> str:
    et_now = datetime.now(pytz.timezone("America/New_York"))
    time_str = et_now.strftime("%Y-%m-%d %H:%M ET")

    spy = get_gex("SPY")
    qqq = get_gex("QQQ")

    msg = f"<b>📊 日内期权结构 · {time_str}</b>\n\n"

    for name, data in [("SPY", spy), ("QQQ", qqq)]:
        if "error" in data:
            msg += f"<b>{name}</b>\n获取失败: {data['error']}\n\n"
            continue

        regime = str(data.get("regime", "—")).upper()
        gex_sign = "🟢 正Gamma" if "POSITIVE" in regime else ("🔴 负Gamma" if "NEGATIVE" in regime else "⚪")

        msg += f"<b>{name}</b>  现价 <code>{data.get('spot')}</code>\n"
        msg += f"Net GEX: <code>{data.get('net_gex')}</code>  {gex_sign}\n"
        msg += f"Call Wall: <code>{data.get('call_wall')}</code>  |  Put Wall: <code>{data.get('put_wall')}</code>\n"
        msg += f"Gamma Flip: <code>{data.get('flip')}</code>\n\n"

    msg += "————————————\n仅供个人学习参考，不构成任何投资建议"
    return msg

if __name__ == "__main__":
    print("正在获取数据并推送...")
    message = build_message()
    print(message)
    send_telegram(message)