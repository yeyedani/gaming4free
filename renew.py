import os, time, json, re, urllib.request
from seleniumbase import SB

# =========================
# CONFIG
# =========================
TARGETS = [
    {"name": "nidaye", "url": "https://g4f.gg/nidaye"}
]

PROXY = "socks5://127.0.0.1:40000"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

# 记忆存储文件
TIME_RECORD_FILE = "g4f_times.json"

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
# Cloudflare / Turnstile检测
# =========================
def has_challenge(sb):
    html = sb.get_page_source().lower()
    return ("turnstile" in html or "verify" in html or "challenge" in html)

# =========================
# JS雷达：找主页面按钮坐标 (修复重名 els1)
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
                    window._target1 = { x: Math.floor(r.left + r.width/2), y: Math.floor(r.top + r.height/2) };
                    break;
                }
            }
        }
        return window._target1;
    """)

# =========================
# JS雷达：找弹窗内确认按钮坐标 (修复重名 els2)
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
                    window._target2 = { x: Math.floor(r.left + r.width/2), y: Math.floor(r.top + r.height/2) };
                    break;
                }
            }
        }
        return window._target2;
    """)

# =========================
# 成功判断（适配最新改版UI）
# =========================
def judge(sb, old_time):
    text = sb.get_text("body").lower()
    
    # 提取时间
    m = re.search(r'\d{2}:\d{2}:\d{2}', text)
    now_time = m.group(0) if m else ""

    # 1. 时间发生变动判定
    changed = (now_time != "") and (now_time != old_time)
    
    # 2. 结合手动截图的新版关键词判定
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
            print(f"[{name}] 打开页面")
            sb.open(url)
            sb.sleep(6)

            if has_challenge(sb):
                print("⚠️ 检测到初始验证页面")

            # =====================
            # 第一阶段：主页按钮雷达 + 物理狙击
            # =====================
            coords1 = scan_main_btn(sb)
            if coords1:
                cx, cy = coords1['x'], coords1['y']
                print(f"[{name}] 雷达锁定主按钮: X={cx}, Y={cy}")
                os.system(f"xdotool mousemove {cx} {cy} click 1")
                time.sleep(0.5)
                os.system(f"xdotool mousemove {cx} {cy} click 1") # 双击确保穿透
            else:
                print(f"[{name}] ⚠️ 主按钮雷达未命中，可能页面未加载完全")
            
            print(f"[{name}] 等待弹窗加载...")
            sb.sleep(4)

            # =====================
            # 第二阶段：弹窗CF验证物理矩阵轰炸
            # =====================
            print(f"[{name}] 启动 CF 验证框物理矩阵轰炸 (无视跨域护盾)...")
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
                print(f"[{name}] 雷达锁定弹窗确认按钮: X={cx2}, Y={cy2}")
                os.system(f"xdotool mousemove {cx2} {cy2} click 1")
            else:
                print(f"[{name}] ⚠️ 弹窗按钮雷达未命中，尝试 JS 强点兜底...")
                # 修复重名 els3
                sb.execute_script("""
                    const els3 = [...document.querySelectorAll('button,a,div,span')];
                    for (let el of els3.reverse()) {
                        const t = (el.innerText || '').toUpperCase();
                        if (t.includes('ADDS 90') || t.includes('VOTE - ADDS')) el.click();
                    }
                """)

            print(f"[{name}] 点击完成，等待 25 秒网络提交与状态刷新...")
            sb.sleep(25)

            # =====================
            # 判断结果与截图
            # =====================
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
    print("===== v3 矩阵轰炸裁决版 (变量修复版) 启动 =====")
    
    os.system("sudo apt-get update > /dev/null 2>&1")
    os.system("sudo apt-get install -y xdotool > /dev/null 2>&1")

    history_times = load_old_times()
    results = []

    for t in TARGETS:
        node_name = t["name"]
        old_time = history_times.get(node_name, "")
        
        r = run_node(t, old_time)
        results.append(r)
        
        if r["time"] and r["time"] != "未知":
            history_times[node_name] = r["time"]

    save_new_times(history_times)

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
