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
            # 1. 深度伪装
            sb.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            sb.sleep(10)
            
            # 2. 阶段一：狙击主 Vote 按钮
            # 【彻底修复】：去掉最外层的 return 关键字，直接让立即执行函数(IIFE)自己计算并吐出结果
            coords = sb.execute_script("""
                (function() {
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
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            
            sb.sleep(8)
            
            # 3. 阶段二：呼吸式 CF 盾检测与轰炸
            print(f"[{name}] 等待验证器就绪...")
            for _ in range(10):
                # 【彻底修复】：去掉这里的 return
                if sb.execute_script("typeof turnstile !== 'undefined'"):
                    break
                time.sleep(2)
            
            print(f"[{name}] 执行物理矩阵轰炸...")
            for y in [540, 560, 580]:
                for x in [810, 830, 850]:
                    os.system(f"xdotool mousemove {x} {y} click 1")
                    time.sleep(0.2)
            
            sb.sleep(12)
            
            # 4. 阶段三：最终确认狙击
            # 【彻底修复】：去掉最外层的 return
            conf = sb.execute_script("""
                (function() {
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
        import traceback
        traceback.print_exc()
        return f"❌ 崩溃: {e}"

# 主逻辑
if __name__ == "__main__":
    results = []
    for t in TARGETS:
        res = run_task(t)
        results.append({"name": t["name"], "status": res})

    tg_msg = "🤖 G4F 自动续期汇报\n" + "\n".join([f"{r['name']}: {r['status']}" for r in results])
    tg(tg_msg)
    print(tg_msg)
