import os, time, json, urllib.request, re
from seleniumbase import SB

TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
]

PROXY = "socks5://127.0.0.1:40000"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

os.system("sudo apt-get update > /dev/null 2>&1")
os.system("sudo apt-get install -y xdotool > /dev/null 2>&1")

def tg(msg):
    if TG_TOKEN and TG_CHAT:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode('utf-8')
            urllib.request.urlopen(urllib.request.Request(url, data, {'Content-Type': 'application/json'}), timeout=10)
        except: pass

def extract_time(text):
    m = re.search(r'\d{2}:\d{2}:\d{2}', text)
    return m.group(0) if m else None

def run_task(target):
    name, url = target["name"], target["url"]
    try:
        with SB(uc=True, proxy=PROXY, headless=False, window_size="1920,1080") as sb:
            sb.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            sb.sleep(10)
            
            # 记录初始时间
            initial_text = sb.get_text("body")
            old_time = extract_time(initial_text)
            print(f"[{name}] 记录初始剩余时间: {old_time}")
            
            # 阶段一：主按钮雷达
            coords = sb.execute_script("""
                return (function() {
                    const els = document.querySelectorAll('button, div, span');
                    for (let e of els) {
                        let txt = (e.innerText || '').toUpperCase();
                        if (txt.includes('ADD 90') || txt.includes('VOTE')) {
                            const r = e.getBoundingClientRect();
                            return [r.left + r.width/2, r.top + r.height/2];
                        }
                    }
                    return null;
                })();
            """)
            
            if coords:
                print(f"[{name}] 锁定主按钮坐标: X={int(coords[0])}, Y={int(coords[1])}")
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            else:
                print(f"[{name}] ⚠️ 严重警告：未找到主页面 Vote 按钮！")
            
            sb.sleep(8)
            
            # 阶段二：CF 盾验证与轰炸
            print(f"[{name}] 等待验证器就绪...")
            for _ in range(10):
                if sb.execute_script("return typeof turnstile !== 'undefined'"):
                    break
                time.sleep(2)
            
            print(f"[{name}] 执行物理矩阵轰炸 (等待CF绿勾)...")
            for y in [540, 560, 580]:
                for x in [810, 830, 850]:
                    os.system(f"xdotool mousemove {x} {y} click 1")
                    time.sleep(0.2)
            
            sb.sleep(12) 
            
            # 阶段三：确认按钮雷达
            conf = sb.execute_script("""
                return (function() {
                    const els = document.querySelectorAll('button, div, span');
                    for (let e of els) {
                        let txt = (e.innerText || '').toUpperCase();
                        if (txt.includes('ADDS 90')) {
                            const r = e.getBoundingClientRect();
                            return [r.left + r.width/2, r.top + r.height/2];
                        }
                    }
                    return null;
                })();
            """)
            
            if conf:
                print(f"[{name}] 锁定弹窗确认按钮坐标: X={int(conf[0])}, Y={int(conf[1])}")
                os.system(f"xdotool mousemove {int(conf[0])} {int(conf[1])} click 1")
            else:
                print(f"[{name}] ⚠️ 严重警告：未找到弹窗中的最终确认按钮！")
            
            # 阶段四：死守倒计时刷新
            print(f"[{name}] 监控提交结果，等待倒计时刷新...")
            success = False
            for i in range(40):
                text = sb.get_text("body")
                new_time = extract_time(text)
                
                # 如果时间发生了变化，且不是空值，说明真正续上了！
                if new_time and old_time and new_time != old_time:
                    print(f"[{name}] 🎉 倒计时已刷新: {old_time} -> {new_time}")
                    success = True
                    break
                time.sleep(1)
            
            sb.save_screenshot(f"screenshots/{name}_final.png")
            
            if success:
                return f"✅ 续期成功 (新时间: {new_time})"
            else:
                return "❌ 续期失败 (时间未变化)"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ 崩溃: {e}"

if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    results = []
    for t in TARGETS:
        res = run_task(t)
        results.append({"name": t["name"], "status": res})

    tg_msg = "🤖 G4F 自动续期汇报\n" + "\n".join([f"{r['name']}: {r['status']}" for r in results])
    tg(tg_msg)
    print(tg_msg)
