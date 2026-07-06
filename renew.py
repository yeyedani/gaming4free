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
            
            # 智能探测：检查当前按钮状态 (是可投票还是冷却中)
            print(f"[{name}] 扫描主控按钮状态...")
            sb.execute_script("""
                window._btn_info = {coords: null, status: 'NOT_FOUND', text: ''};
                var els1 = document.querySelectorAll('button, a, div, span');
                for (var i = els1.length - 1; i >= 0; i--) {
                    var txt = (els1[i].innerText || '').toUpperCase();
                    if (els1[i].getBoundingClientRect().width < 500) {
                        if (txt.includes('WAIT ') && txt.includes(' MIN')) {
                            window._btn_info = {coords: null, status: 'COOLDOWN', text: txt};
                            break;
                        } else if (txt.includes('+ VOTE +') || txt.includes('ADD 90')) {
                            var r = els1[i].getBoundingClientRect();
                            if (r.width > 0 && r.height > 0) {
                                var ui_offset = window.outerHeight - window.innerHeight;
                                var sx = window.screenX || 0;
                                var sy = window.screenY || 0;
                                window._btn_info = {coords: [Math.floor(sx + r.left + r.width/2), Math.floor(sy + ui_offset + r.top + r.height/2)], status: 'READY', text: txt};
                                break;
                            }
                        }
                    }
                }
            """)
            btn_info = sb.evaluate("window._btn_info")
            
            if btn_info['status'] == 'COOLDOWN':
                # 清洗换行符，提取出 WAIT 5 MIN 这种纯净文本
                cool_text = btn_info['text'].replace('\n', ' ').strip()
                print(f"[{name}] 🛑 处于冷却期: {cool_text}")
                return f"⏳ 冷却中 ({cool_text})"
                
            elif btn_info['status'] == 'READY' and btn_info['coords']:
                coords = btn_info['coords']
                print(f"[{name}] 锁定真实主按钮坐标: X={int(coords[0])}, Y={int(coords[1])}")
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            else:
                print(f"[{name}] ⚠️ 未找到任何有效的主控按钮！")
                return "❌ 异常 (未找到按钮)"
            
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
            
            print(f"[{name}] 扫描弹窗确认按钮...")
            conf = None
            for _ in range(15):
                sb.execute_script("""
                    window._conf_coords = null;
                    var els2 = document.querySelectorAll('button, a, div, span');
                    for (var j = els2.length - 1; j >= 0; j--) {
                        var txt = (els2[j].innerText || '').toUpperCase();
                        if ((txt.includes('ADDS 90 MINUTES') || txt.includes('VOTE - ADDS')) && els2[j].getBoundingClientRect().width < 500) {
                            var r = els2[j].getBoundingClientRect();
                            if (r.width > 0 && r.height > 0) { 
                                var ui_offset = window.outerHeight - window.innerHeight;
                                var sx = window.screenX || 0;
                                var sy = window.screenY || 0;
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
            
            # 【终极判定逻辑】抓取页面成功弹字提示
            print(f"[{name}] 监控提交结果，等待弹窗成功提示...")
            success = False
            for i in range(40):
                text = sb.get_text("body").lower()
                
                # 抓取您截图里出现的精准提示词
                if "90 minutes added!" in text or "minutes added" in text:
                    print(f"[{name}] 🎉 成功捕获到续期确认弹窗提示！")
                    success = True
                    break
                time.sleep(1)
            
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot(f"screenshots/{name}_final.png")
            
            if success:
                return f"✅ 续期成功 (已捕获成功提示)"
            else:
                return f"❌ 续期失败 (未监测到成功提示)"

    except Exception as e:
        traceback.print_exc()
        return f"❌ 崩溃: {e}"

if __name__ == "__main__":
    print("\n===== 智能全状态接管版 启动 =====")
    results = []
    for t in TARGETS:
        res = run_task(t)
        results.append({"name": t["name"], "status": res})

    tg_msg = "🤖 G4F 续期报告\n-------------------\n" + "\n".join([f"节点: {r['name']}\n状态: {r['status']}\n-------------------" for r in results])
    tg(tg_msg)
    print(tg_msg)
