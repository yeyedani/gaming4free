import os, time, json, urllib.request, re
from seleniumbase import SB

TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
]

PROXY = "socks5://127.0.0.1:40000"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

# 确保依赖存在
os.system("sudo apt-get update > /dev/null 2>&1")
os.system("sudo apt-get install -y xdotool > /dev/null 2>&1")

def tg(msg):
    if TG_TOKEN and TG_CHAT:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode('utf-8')
            urllib.request.urlopen(urllib.request.Request(url, data, {'Content-Type': 'application/json'}), timeout=10)
        except: pass

def run_task(target):
    name, url = target["name"], target["url"]
    try:
        with SB(uc=True, proxy=PROXY, headless=False, window_size="1920,1080") as sb:
            sb.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            sb.sleep(10)
            
            # 【修复版雷达】使用匿名函数包裹 return
            coords = sb.execute_script("""
                return (function() {
                    const el = [...document.querySelectorAll('button, div, span')].find(e => 
                        e.innerText.toUpperCase().includes('ADD 90') || e.innerText.toUpperCase().includes('VOTE')
                    );
                    if (el) {
                        const r = el.getBoundingClientRect();
                        return [r.left + r.width/2, r.top + r.height/2];
                    }
                    return null;
                })();
            """)
            if coords:
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            
            sb.sleep(8)
            
            # 【修复版确认狙击】使用匿名函数包裹 return
            conf = sb.execute_script("""
                return (function() {
                    const el = [...document.querySelectorAll('button, div, span')].find(e => 
                        e.innerText.toUpperCase().includes('ADDS 90')
                    );
                    if (el) {
                        const r = el.getBoundingClientRect();
                        return [r.left + r.width/2, r.top + r.height/2];
                    }
                    return null;
                })();
            """)
            if conf:
                os.system(f"xdotool mousemove {int(conf[0])} {int(conf[1])} click 1")
            
            sb.sleep(20)
            sb.save_screenshot(f"{name}_final.png")
            return "✅ 已尝试点击"

    except Exception as e:
        return f"❌ 崩溃: {e}"

results = []
for t in TARGETS:
    res = run_task(t)
    results.append({"name": t["name"], "status": res})

tg_msg = "🤖 G4F 自动续期汇报\n" + "\n".join([f"{r['name']}: {r['status']}" for r in results])
tg(tg_msg)
print(tg_msg)
