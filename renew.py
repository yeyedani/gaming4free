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

def run_task(target):
    name, url = target["name"], target["url"]
    try:
        with SB(uc=True, proxy=PROXY, headless=False, window_size="1920,1080") as sb:
            print(f"[{name}] 打开页面")
            # 隐藏 webdriver 指纹 (try包裹防止部分环境二次注入报错)
            try:
                sb.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except:
                pass
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            
            print(f"[{name}] 等待 Cloudflare...")
            sb.sleep(10)
            
            initial_text = sb.get_text("body")
            old_time = extract_time(initial_text)
            print(f"[{name}] 记录初始剩余时间: {old_time}")
            
            print(f"[{name}] 寻找 Vote 按钮...")
            # 【彻底断绝报错】：整段 JS 零 return，只做变量赋值
            sb.execute_script("""
                window._btn_coords = null;
                let els1 = document.querySelectorAll('button, div, span');
                for (let i = 0; i < els1.length; i++) {
                    let txt = (els1[i].innerText || '').toUpperCase();
                    if (txt.includes('ADD 90') || txt.includes('VOTE')) {
                        let r = els1[i].getBoundingClientRect();
                        window._btn_coords = [r.left + r.width/2, r.top + r.height/2];
                        break;
                    }
                }
            """)
            # 使用 sb.evaluate 直接读取全局变量，绕过 execute_script 的返回值包裹机制
            coords = sb.evaluate("window._btn_coords")
            
            if coords:
                print(f"[{name}] 锁定主按钮坐标: X={int(coords[0])}, Y={int(coords[1])}")
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            else:
                print(f"[{name}] ⚠️ 未找到主页面 Vote 按钮！")
            
            sb.sleep(8)
            
            print(f"[{name}] 等待验证器就绪...")
            for _ in range(10):
                # 直接 evaluate 表达式，绝不写 return
                is_ready = sb.evaluate("typeof turnstile !== 'undefined'")
                if is_ready:
                    break
                time.sleep(2)
            
            print(f"[{name}] 执行物理矩阵轰炸 (等待CF绿勾)...")
            for y in [540, 560, 580]:
                for x in [810, 830, 850]:
                    os.system(f"xdotool mousemove {x} {y} click 1")
                    time.sleep(0.2)
            
            sb.sleep(12) 
            
            print(f"[{name}] 寻找确认按钮...")
            # 【彻底断绝报错】：弹窗雷达同理，零 return
            sb.execute_script("""
                window._conf_coords = null;
                let els2 = document.querySelectorAll('button, div, span');
                for (let i = 0; i < els2.length; i++) {
                    let txt = (els2[i].innerText || '').toUpperCase();
                    if (txt.includes('ADDS 90')) {
                        let r = els2[i].getBoundingClientRect();
                        window._conf_coords = [r.left + r.width/2, r.top + r.height/2];
                        break;
                    }
                }
            """)
            conf = sb.evaluate("window._conf_coords")
            
            if conf:
                print(f"[{name}] 锁定弹窗确认按钮坐标: X={int(conf[0])}, Y={int(conf[1])}")
                os.system(f"xdotool mousemove {int(conf[0])} {int(conf[1])} click 1")
            else:
                print(f"[{name}] ⚠️ 未找到弹窗中的最终确认按钮！")
            
            print(f"[{name}] 监控提交结果，等待倒计时刷新...")
            success = False
            new_time = None
            for i in range(40):
                text = sb.get_text("body")
                new_time = extract_time(text)
                if new_time and old_time and new_time != old_time:
                    print(f"[{name}] 🎉 倒计时已刷新: {old_time} -> {new_time}")
                    success = True
                    break
                time.sleep(1)
            
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot(f"screenshots/{name}_final.png")
            
            if success:
                return f"✅ 续期成功 (新时间: {new_time})"
            else:
                return "❌ 续期失败 (时间未变化)"

    except Exception as e:
        traceback.print_exc()
        return f"❌ 崩溃: {e}"

if __name__ == "__main__":
    print("\n===== v6 无Return绝对防护版 启动 =====")
    results = []
    for t in TARGETS:
        res = run_task(t)
        results.append({"name": t["name"], "status": res})

    tg_msg = "🤖 G4F 续期报告\n-------------------\n" + "\n".join([f"节点: {r['name']}\n状态: {r['status']}\n-------------------" for r in results])
    tg(tg_msg)
    print(tg_msg)
