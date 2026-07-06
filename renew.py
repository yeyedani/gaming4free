import os, time, json, re, urllib.request
from seleniumbase import SB

TARGETS = [
    {"name": "nidaye", "url": "https://g4f.gg/nidaye"}
]

PROXY = "socks5://127.0.0.1:40000"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

TIME_FILE = "g4f_times.json"


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
# 时间记忆管理 (持久化)
# =========================
def load_old_times():
    if os.path.exists(TIME_RECORD_FILE):
        try:
            with open(TIME_RECORD_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_new_times(times_dict):
    try:
        with open(TIME_RECORD_FILE, 'w') as f:
            json.dump(times_dict, f)
    except:
        pass

# =========================
# CF 等待
# =========================
def wait_cf(sb):
    try:
        sb.wait_for_ready_state_complete(timeout=30)
    except:
        pass
    for _ in range(30):
        html = sb.get_page_source().lower()
        if "turnstile" not in html and "challenge" not in html:
            break
        time.sleep(1)


# =========================
# JS雷达：找主页面按钮坐标 (加入绝对屏幕坐标修正)
# =========================
def scan_main_btn(sb):
    return sb.execute_script("""
        window._target1 = null;
        const els1 = [...document.querySelectorAll('button,a,div,span')];
        for (let el of els1.reverse()) {
            const t = (el.innerText || '').toUpperCase().replace(/\\s+/g,' ');
            if (t.includes('ADD 90') || t.includes('+ VOTE +')) {
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {
                    // 精准计算真实的屏幕物理坐标 (包含浏览器UI的高度补偿)
                    let screenX = window.screenX || 0;
                    let screenY = (window.screenY || 0) + (window.outerHeight - window.innerHeight);
                    window._target1 = { 
                        x: Math.floor(screenX + r.left + r.width/2), 
                        y: Math.floor(screenY + r.top + r.height/2) 
                    };
                    break;
                }
            }
        }
        return window._target1;
    """)

# =========================
# JS雷达：找弹窗内确认按钮坐标 (加入绝对屏幕坐标修正)
# =========================
def scan_confirm_btn(sb):
    return sb.execute_script("""
        window._target2 = null;
        const els2 = [...document.querySelectorAll('button,a,div,span')];
        for (let el of els2.reverse()) {
            const t = (el.innerText || '').toUpperCase().replace(/\\s+/g,' ');
            if (t.includes('ADDS 90 MINUTES') || t.includes('VOTE - ADDS')) {
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {
                    let screenX = window.screenX || 0;
                    let screenY = (window.screenY || 0) + (window.outerHeight - window.innerHeight);
                    window._target2 = { 
                        x: Math.floor(screenX + r.left + r.width/2), 
                        y: Math.floor(screenY + r.top + r.height/2) 
                    };
                    break;
                }
            }
        }
        return window._target2;
    """)


# =========================
# 时间与状态裁判
# =========================
def judge(sb, old_time):
    text = sb.get_text("body").lower()
    
    m = re.search(r'\d{2}:\d{2}:\d{2}', text)
    now_time = m.group(0) if m else ""

    changed = (now_time != "") and (now_time != old_time)
    
    keywords = ["wait 5 min", "wait 4 min", "+90m", "90 minutes added", "extended this server recently"]
    hit = any(k in text for k in keywords)

    if hit:
        status = "✅ 成功 (特征文字命中)"
    elif changed:
        status = "✅ 成功 (倒计时已刷新)"
    else:
        status = "⚠️ 状态未知"

    return status, now_time


# =========================
# 单节点执行
# =========================
def run_node(t, old_time):
    name = t["name"]
    url = t["url"]
    
    try:
        with SB(
            uc=True,
            headless=False,
            proxy=PROXY,
            window_size="1920,1080"
        ) as sb:
            print(f"[{name}] 打开页面并重置视口坐标...")
            # 核心修正：将浏览器死死钉在屏幕 0,0 位置
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            
            wait_cf(sb)

            # =====================
            # 第一阶段：主页按钮雷达 + 物理狙击
            # =====================
            coords1 = scan_main_btn(sb)
            if coords1:
                cx, cy = coords1['x'], coords1['y']
                print(f"[{name}] 雷达锁定主按钮 绝对坐标: X={cx}, Y={cy}")
                os.system(f"xdotool mousemove {cx} {cy} click 1")
                time.sleep(0.5)
                os.system(f"xdotool mousemove {cx} {cy} click 1")
            else:
                print(f"[{name}] ⚠️ 主按钮雷达未命中，可能页面未加载完全")
            
            print(f"[{name}] 等待弹窗加载...")
            sb.sleep(5)

            # =====================
            # 第二阶段：弹窗CF验证物理矩阵轰炸
            # =====================
            print(f"[{name}] 启动 CF 验证框物理矩阵轰炸...")
            # 因为浏览器强制对齐 0,0，这套固定矩阵绝对能精准覆盖 CF 框
            xs = [810, 830, 850, 870]
            ys = [530, 550, 570, 590]
            
            for y in ys:
                for x in xs:
                    os.system(f"xdotool mousemove {x} {y} click 1")
                    time.sleep(0.08) 
            
            print(f"[{name}] 轰炸完毕，等待 CF 验证通过...")
            sb.sleep(8) 

            # =====================
            # 第三阶段：弹窗确认按钮雷达 + 物理狙击
            # =====================
            coords2 = scan_confirm_btn(sb)
            if coords2:
                cx2, cy2 = coords2['x'], coords2['y']
                print(f"[{name}] 雷达锁定弹窗确认按钮 绝对坐标: X={cx2}, Y={cy2}")
                os.system(f"xdotool mousemove {cx2} {cy2} click 1")
            else:
                print(f"[{name}] ⚠️ 弹窗按钮雷达未命中，尝试 JS 强点兜底...")
                sb.execute_script("""
                    const els3 = [...document.querySelectorAll('button,a,div,span')];
                    for (let el of els3.reverse()) {
                        const t = (el.innerText || '').toUpperCase();
                        if (t.includes('ADDS 90') || t.includes('VOTE - ADDS')) el.click();
                    }
                """)

            print(f"[{name}] 点击完成，等待网络提交与状态刷新...")
            sb.sleep(25)

            status, ttime = judge(sb, old_time)
            
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot(f"screenshots/{name}_final.png")

            return {
                "name": name,
                "status": status,
                "time": ttime
            }

    except Exception as e:
        return {
            "name": name,
            "status": f"❌ 崩溃: {e}",
            "time": "未知"
        }

# =========================
# 主程序
# =========================
def main():
    print("===== v3.3 绝对命中修正版 启动 =====")
    
    os.system("sudo apt-get update > /dev/null 2>&1")
    os.system("sudo apt-get install -y xdotool > /dev/null 2>&1")

    history_times = {}
    if os.path.exists(TIME_FILE):
        try:
            history_times = json.load(open(TIME_FILE))
        except:
            pass
            
    results = []

    for t in TARGETS:
        node_name = t["name"]
        old_time = history_times.get(node_name, "")
        
        r = run_node(t, old_time)
        results.append(r)
        
        if r["time"] and r["time"] != "未知":
            history_times[node_name] = r["time"]

    try:
        json.dump(history_times, open(TIME_FILE, "w"))
    except:
        pass

    msg = ["🤖 v3 自动续期终极报告"]
    for r in results:
        msg.append("-------------------")
        msg.append(f"节点: {r['name']}")
        msg.append(f"状态: {r['status']}")
        msg.append(f"时间: {r['time']}")

    report_text = "\n".join(msg)
    tg(report_text)
    print("\n" + report_text)

if __name__ == "__main__":
    main()
