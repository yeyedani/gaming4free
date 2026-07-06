import os, time, json, urllib.request, re
from seleniumbase import SB

# =========================
# CONFIG
# =========================
TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
]

PROXY = "socks5://127.0.0.1:40000"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# =========================
# Telegram
# =========================
def tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode()
        req = urllib.request.Request(url, data, {"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except:
        pass


# =========================
# Cloudflare 判断
# =========================
def wait_cloudflare(sb, timeout=30):
    for _ in range(timeout):
        html = sb.get_page_source().lower()
        if "turnstile" not in html and "challenge" not in html:
            return True
        time.sleep(1)
    return False


# =========================
# 安全 JS 执行（全部封装，避免污染）
# =========================
def js_find_button(sb, keyword):
    return sb.execute_script(f"""
        return (function() {{
            const els = Array.from(document.querySelectorAll('button,div,span,a'));
            for (let i = 0; i < els.length; i++) {{
                const t = (els[i].innerText || '').toUpperCase();
                if (t.includes('{keyword}')) {{
                    const r = els[i].getBoundingClientRect();
                    if (r.width > 0 && r.height > 0) {{
                        return {{
                            x: Math.floor(r.left + r.width/2),
                            y: Math.floor(r.top + r.height/2)
                        }};
                    }}
                }}
            }}
            return null;
        }})();
    """)


def safe_click(sb, coords):
    if not coords:
        return False
    x, y = int(coords["x"]), int(coords["y"])
    os.system(f"xdotool mousemove {x} {y} click 1")
    return True


# =========================
# 主流程
# =========================
def run_task(t):
    name = t["name"]
    url = t["url"]

    try:
        with SB(
            uc=True,
            proxy=PROXY,
            headless=False,
            window_size="1920,1080"
        ) as sb:

            print(f"[{name}] 打开页面")
            sb.open(url)
            sb.sleep(8)

            # =========================
            # CF 等待（稳定版，不轰炸）
            # =========================
            print(f"[{name}] 等待 Cloudflare...")
            wait_cloudflare(sb)

            # =========================
            # Step 1: 主按钮
            # =========================
            print(f"[{name}] 寻找 Vote 按钮...")
            btn = js_find_button(sb, "ADD 90")
            if not btn:
                btn = js_find_button(sb, "VOTE")

            if btn:
                print(f"[{name}] 点击主按钮 {btn}")
                safe_click(sb, btn)

            sb.sleep(6)

            # =========================
            # Step 2: 弹窗确认按钮
            # =========================
            print(f"[{name}] 寻找确认按钮...")
            confirm = js_find_button(sb, "ADDS 90")
            if confirm:
                print(f"[{name}] 点击确认 {confirm}")
                safe_click(sb, confirm)
            else:
                print(f"[{name}] JS fallback click")
                sb.execute_script("""
                    (function(){
                        const els = Array.from(document.querySelectorAll('button,div,span,a'));
                        for (let i=0;i<els.length;i++){
                            const t = (els[i].innerText || '').toUpperCase();
                            if (t.includes('ADDS 90') || t.includes('VOTE')) {
                                els[i].click();
                                break;
                            }
                        }
                    })();
                """)

            # =========================
            # Step 3: 等待结果
            # =========================
            print(f"[{name}] 等待结果...")
            success = False

            for _ in range(25):
                text = sb.get_text("body").lower()

                if ("+90" in text or "wait" in text or "voted" in text):
                    success = True
                    break

                time.sleep(1)

            # =========================
            # 截图
            # =========================
            path = f"{SCREENSHOT_DIR}/{name}_final.png"
            sb.save_screenshot(path)

            return {
                "name": name,
                "status": "✅ 成功" if success else "⚠️ 未确认",
                "screenshot": path
            }

    except Exception as e:
        return {
            "name": name,
            "status": f"❌ 崩溃: {e}",
            "screenshot": ""
        }


# =========================
# MAIN
# =========================
def main():
    print("===== v5 稳定守护版 启动 =====")

    results = []
    for t in TARGETS:
        r = run_task(t)
        results.append(r)

    msg = ["🤖 G4F 续期报告"]
    for r in results:
        msg.append("-------------------")
        msg.append(f"节点: {r['name']}")
        msg.append(f"状态: {r['status']}")
        msg.append(f"截图: {r['screenshot']}")

    tg("\n".join(msg))
    print("\n".join(msg))


if __name__ == "__main__":
    main()
