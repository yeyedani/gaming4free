import os, time, json, urllib.request, re, traceback
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

def time_to_seconds(t_str):
    if not t_str: return 0
    h, m, s = map(int, t_str.split(':'))
    return h * 3600 + m * 60 + s

def run_task(target):
    name, url = target["name"], target["url"]
    try:
        with SB(uc=True, proxy=PROXY, headless=False, window_size="1920,1080") as sb:
            print(f"[{name}] 打开页面")
            try:
                sb.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except: pass
            
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            
            print(f"[{name}] 等待网页加载...")
            sb.sleep(10)
            
            initial_text = sb.get_text("body")
            old_time = extract_time(initial_text)
            old_sec = time_to_seconds(old_time)
            print(f"[{name}] 记录初始剩余时间: {old_time}")
            
            print(f"[{name}] 寻找 Vote 按钮...")
            sb.execute_script("""
                window._btn_coords = null;
                let els1 = document.querySelectorAll('button, div, span');
                for (let i = 0; i < els1.length; i++) {
                    let txt = (els1[i].innerText || '').toUpperCase();
                    if (txt.includes('ADD 90') || txt.includes('VOTE')) {
                        let r = els1[i].getBoundingClientRect();
                        if (r.width > 0 && r.height > 0) {
                            let ui_offset = window.outerHeight - window.innerHeight;
                            let sx = window.screenX || 0;
                            let sy = window.screenY || 0;
                            window._btn_coords = [Math.floor(sx + r.left + r.width/2), Math.floor(sy + ui_offset + r.top + r.height/2)];
                            break;
                        }
                    }
                }
            """)
            coords = sb.evaluate("window._btn_coords")
            
            if coords:
                print(f"[{name}] 锁定主按钮坐标: X={int(coords[0])}, Y={int(coords[1])}")
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            else:
                print(f"[{name}] ⚠️ 未找到主页面 Vote 按钮！")
            
            sb.sleep(6)
            
            print(f"[{name}] 等待验证器就绪...")
            for _ in range(10):
                if sb.evaluate("typeof turnstile !== 'undefined'"):
                    break
                time.sleep(2)
            
            print(f"[{name}] 执行物理矩阵轰炸 (等待CF绿勾)...")
            for y in [540, 560, 580]:
                for x in [810, 830, 850]:
                    os.system(f"xdotool mousemove {x} {y} click 1")
                    time.sleep(0.2)
            
            # 【终极修复】：轮询等待真正的确认按钮出现，绝不点 0,0
            print(f"[{name}] 扫描弹窗确认按钮...")
            conf = None
            for _ in range(15): # 给 CF 盾 15秒的时间转绿勾
                sb.execute_script("""
                    window._conf_coords = null;
                    let els2 = document.querySelectorAll('button, div, span');
                    for (let i = 0; i < els2.length; i++) {
                        let txt = (els2[i].innerText || '').toUpperCase();
                        if (txt.includes('ADDS 90 MINUTES') || txt.includes('VOTE - ADDS')) {
                            let r = els2[i].getBoundingClientRect();
                            if (r.width > 0 && r.height > 0) { // 必须是真实可见的按钮
                                let ui_offset = window.outerHeight - window.innerHeight;
                                let sx = window.screenX || 0;
                                let sy = window.screenY || 0;
                                window._conf_coords = [Math.floor(sx + r.left + r.width/2), Math.floor(sy + ui_offset + r.top + r.height/2)];
                                break;
                            }
                        }
                    }
                """)
                conf = sb.evaluate("window._conf_coords")
                if conf:
                    break
                time.sleep(1)
            
            if conf:
                print(f"[{name}] 锁定真实确认按钮坐标: X={int(conf[0])}, Y={int(conf[1])}")
                os.system(f"xdotool mousemove {int(conf[0])} {int(conf[1])} click 1")
            else:
                print(f"[{name}] ⚠️ 等待超时，未找到可见的最终确认按钮！")
            
            print(f"[{name}] 监控提交结果，等待倒计时暴涨...")
            success = False
            new_time = None
            for i in range(40):
                text = sb.get_text("body")
                new_time = extract_time(text)
                new_sec = time_to_seconds(new_time)
                
                # 时间必须实打实地增加了至少 1 小时 (3600秒) 才算真成功！
                if new_sec > old_sec + 3600:
                    print(f"[{name}] 🎉 倒计时已暴涨: {old_time} -> {new_time}")
                    success = True
                    break
                time.sleep(1)
            
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot(f"screenshots/{name}_final.png")
            
            if success:
                return f"✅ 续期成功 (新时间: {new_time})"
            else:
                return f"❌ 续期失败 (最终时间: {new_time})"

    except Exception as e:
        traceback.print_exc()
        return f"❌ 崩溃: {e}"

if __name__ == "__main__":
    print("\n===== v7 真理审判版 启动 =====")
    results = []
    for t in TARGETS:
        res = run_task(t)
        results.append({"name": t["name"], "status": res})

    tg_msg = "🤖 G4F 续期报告\n-------------------\n" + "\n".join([f"节点: {r['name']}\n状态: {r['status']}\n-------------------" for r in results])
    tg(tg_msg)
    print(tg_msg)
