import os, time, json, re, urllib.request
from seleniumbase import SB

# =========================
# CONFIG
# =========================
TARGETS = [
    {"name": "nidaye", "url": "https://g4f.gg/nidaye"}
]

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

PROXY = "socks5://127.0.0.1:40000"

# =========================
# TG 通知
# =========================
def send_tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("TG失败:", e)

# =========================
# 判断成功核心逻辑（工业版）
# =========================
def judge(page_text, old_time):
    text = page_text.lower()

    time_match = re.search(r'\d{2}:\d{2}:\d{2}', page_text)
    current_time = time_match.group(0) if time_match else ""

    # 1. 时间变化（最可靠）
    time_changed = current_time and current_time != old_time

    # 2. 成功关键词（扩展）
    keywords = [
        "90 minutes",
        "added",
        "success",
        "vote",
        "完成",
        "成功",
        "extended",
    ]
    hit_keyword = any(k in text for k in keywords)

    # 3. 综合判断
    if time_changed or hit_keyword:
        status = "✅ 续期成功"
    elif current_time:
        status = "⚠️ 已加载但未确认"
    else:
        status = "❌ 页面异常"

    return status, current_time


# =========================
# 主逻辑
# =========================
def run_target(name, url):

    old_time = os.getenv(f"LAST_TIME_{name}", "")
    result = {
        "name": name,
        "status": "❌ 未执行",
        "time": "未知"
    }

    for attempt in range(3):  # ⭐ 自动重试
        try:
            print(f"[{name}] 第 {attempt+1} 次尝试")

            with SB(
                uc=True,
                proxy=PROXY,
                headless=False,
                window_size="1920,1080"
            ) as sb:

                sb.open(url)
                sb.sleep(6)

                # ======================
                # 1. 点击主页按钮（稳健版）
                # ======================
                try:
                    sb.uc_click("text=ADD 90 MIN", timeout=5)
                except:
                    sb.execute_script("""
                        [...document.querySelectorAll('button,a,div,span')]
                        .reverse()
                        .forEach(e=>{
                            if((e.innerText||'').toLowerCase().includes('add 90')){
                                e.click();
                            }
                        });
                    """)

                sb.sleep(4)

                # ======================
                # 2. 弹窗确认
                # ======================
                try:
                    sb.uc_click("text=90 MIN", timeout=5)
                except:
                    sb.execute_script("""
                        [...document.querySelectorAll('button,a,div,span')]
                        .forEach(e=>{
                            if((e.innerText||'').toLowerCase().includes('90')){
                                e.click();
                            }
                        });
                    """)

                sb.sleep(20)

                # ======================
                # 3. 结果分析
                # ======================
                page_text = sb.get_text("body")

                status, current_time = judge(page_text, old_time)

                result["status"] = status
                result["time"] = current_time or "未知"

                # 保存时间状态
                if current_time:
                    os.environ[f"LAST_TIME_{name}"] = current_time

                # 截图
                os.makedirs("screenshots", exist_ok=True)
                sb.save_screenshot(f"screenshots/{name}.png")

                return result

        except Exception as e:
            print(f"[{name}] 失败:", e)
            time.sleep(5)

    result["status"] = "❌ 连续失败"
    return result


# =========================
# 执行全部节点
# =========================
print("===== G4F 稳定挂机启动 =====")

results = []

for t in TARGETS:
    r = run_target(t["name"], t["url"])
    results.append(r)

# =========================
# 汇总报告
# =========================
msg = ["🤖 G4F 稳定续期报告"]

for r in results:
    msg.append("-------------------")
    msg.append(f"节点: {r['name']}")
    msg.append(f"状态: {r['status']}")
    msg.append(f"时间: {r['time']}")

final_msg = "\n".join(msg)

print(final_msg)
send_tg(final_msg)
