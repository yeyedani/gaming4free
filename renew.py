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
            # 1. 深度伪装：抹除 WebDriver 指纹
            sb.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            sb.sleep(10) # 给页面充足的初始化时间
            
            # 2. 阶段一：狙击主 Vote 按钮
            coords = sb.execute_script("""
                const el = [...document.querySelectorAll('button, div, span')].find(e => 
                    e.innerText.toUpperCase().includes('ADD 90') || e.innerText.toUpperCase().includes('VOTE')
                );
                if (el) {
                    const r = el.getBoundingClientRect();
                    return [r.left + r.width/2, r.top + r.height/2];
                }
                return null;
            """)
            if coords:
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            
            sb.sleep(8) # 等待弹窗弹出
            
            # 3. 阶段二：呼吸式 CF 盾检测与轰炸
            print(f"[{name}] 等待验证器就绪...")
            for _ in range(10): # 循环检测验证器是否存在
                if sb.execute_script("return typeof turnstile !== 'undefined'"):
                    break
                time.sleep(2)
            
            print(f"[{name}] 执行物理矩阵轰炸...")
            for y in [540, 560, 580]:
                for x in [810, 830, 850]:
                    os.system(f"xdotool mousemove {x} {y} click 1")
                    time.sleep(0.2)
            
            sb.sleep(12) # 等待绿勾出现
            
            # 4. 阶段三：最终确认狙击
            conf = sb.execute_script("""
                const el = [...document.querySelectorAll('button, div, span')].find(e => 
                    e.innerText.toUpperCase().includes('ADDS 90')
                );
                if (el) {
                    const r = el.getBoundingClientRect();
                    return [r.left + r.width/2, r.top + r.height/2];
                }
                return null;
            """)
            if conf:
                os.system(f"xdotool mousemove {int(conf[0])} {int(conf[1])} click 1")
            
            # 5. 阶段四：监听 API 状态
            print(f"[{name}] 监控提交结果...")
            success = False
            for _ in range(40):
                text = sb.get_text("body").lower()
                if "voted" in text or "+90" in text or "wait" in text:
                    success = True
                    break
                time.sleep(1)
            
            sb.save_screenshot(f"{name}_final.png")
            return f"{'✅ 续期成功' if success else '⚠️ 状态未知'}"

    except Exception as e:
        return f"❌ 崩溃: {e}"

# 主逻辑
results = []
for t in TARGETS:
    res = run_task(t)
    results.append({"name": t["name"], "status": res, "time": "已结算"})

tg_msg = "🤖 G4F 自动续期汇报\n" + "\n".join([f"{r['name']}: {r['status']}" for r in results])
tg(tg_msg)
print(tg_msg)
