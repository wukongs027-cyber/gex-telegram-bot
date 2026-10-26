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
    weekday = et_now.strftime("%A")

    tickers = ["SPY", "QQQ", "AAPL", "NVDA"]
    results = {t: get_gex(t) for t in tickers}

    msg = f"<b>📊 日内期权结构</b>\n"
    msg += f"<code>{time_str}  ({weekday})</code>\n"
    msg += "────────────────\n\n"

    for name in tickers:
        data = results[name]
        if "error" in data:
            msg += f"<b>{name}</b>  获取失败\n<code>{data['error']}</code>\n\n"
            continue

        spot = data.get("spot", "—")
        net_gex = data.get("net_gex", "—")
        call_wall = data.get("call_wall", "—")
        put_wall = data.get("put_wall", "—")
        flip = data.get("flip", "—")
        regime = str(data.get("regime", "")).upper()

        if "POSITIVE" in regime:
            gex_icon = "🟢 正Gamma（偏震荡）"
        elif "NEGATIVE" in regime:
            gex_icon = "🔴 负Gamma（易加速）"
        else:
            gex_icon = "⚪ 状态未知"

        msg += f"<b>{name}</b>   现价 <code>{spot}</code>\n"
        msg += f"{gex_icon}\n"
        msg += f"Net GEX: <code>{net_gex}</code>\n"
        msg += f"Call Wall: <code>{call_wall}</code>   Put Wall: <code>{put_wall}</code>\n"
        msg += f"Gamma Flip: <code>{flip}</code>\n\n"

    msg += "────────────────\n"
    msg += "<i>仅供个人学习参考，不构成投资建议</i>"
    return msg

if __name__ == "__main__":
    print("正在获取数据并推送...")
    message = build_message()
    print(message)
    send_telegram(message)