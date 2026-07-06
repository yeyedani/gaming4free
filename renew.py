import os, sys, time, urllib.request, json, re
from seleniumbase import SB

# ==========================================
# 💡 G4F.GG 自动续期 (物理狙击破盾版)
# ==========================================
TARGETS = [
    {"name": "renqi", "url": "https://g4f.gg/renqi"},
    {"name": "heisi", "url": "https://g4f.gg/heisi"}
]

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

def send_unified_tg(results):
    if TG_TOKEN and TG_CHAT:
        try:
            lines = ["🤖 G4F 续期综合汇报"]
            for res in results:
                lines.append(f"节点: {res['name']} | 状态: {res['status']} | 时间: {res['time']}")
            msg = "\n".join(lines)
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode('utf-8')
            urllib.request.urlopen(urllib.request.Request(url, data, {'Content-Type': 'application/json'}), timeout=10)
        except Exception as e:
            print(f"发送通知失败: {e}")

# 安装环境依赖
os.system("sudo apt-get update > /dev/null 2>&1")
os.system("sudo apt-get install -y xdotool > /dev/null 2>&1")

task_results = []
proxy_str = "socks5://127.0.0.1:40000"

for target in TARGETS:
    name = target["name"]
    url = target["url"]
    
    try:
        # 深度伪装：隐藏 WebDriver 指纹
        with SB(uc=True, proxy=proxy_str, headless=False, window_size="1920,1080") as sb:
            sb.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            sb.sleep(8) 
            
            # 【物理狙击阶段 1】探测按钮坐标并点击
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
                print(f"[{name}] 发现按钮坐标: {coords}")
                os.system(f"xdotool mousemove {int(coords[0])} {int(coords[1])} click 1")
            
            sb.sleep(6) # 等待 CF 盾加载
            
            # 【物理轰炸阶段 2】地毯式轰炸 CF 验证勾选框
            # 针对 1920x1080 下弹窗区域的验证框 (需根据截图微调坐标)
            print(f"[{name}] 开始 CF 盾物理矩阵轰炸...")
            for y in [540, 560, 580]:
                for x in [800, 830, 860]:
                    os.system(f"xdotool mousemove {x} {y} click 1")
                    time.sleep(0.1)
            
            sb.sleep(10) # 等待打勾
            
            # 【最终结算】
            page_text = sb.get_text("body").lower()
            time_match = re.search(r'\d{2}:\d{2}:\d{2}', page_text)
            rem = time_match.group(0) if time_match else "未知"
            status = "✅ 成功" if ("90 minutes" in page_text or "extended" in page_text) else "⚠️ 未知"
            
            task_results.append({"name": name, "status": status, "time": rem})
            sb.save_screenshot(f"{name}_final.png")
            
    except Exception as e:
        task_results.append({"name": name, "status": "❌ 失败", "time": "未知"})

send_unified_tg(task_results)
