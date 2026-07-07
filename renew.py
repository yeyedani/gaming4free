import os, sys, time, urllib.request, json, re
from seleniumbase import SB

# ==========================================
# 💡 G4F.GG 自动续期
# ==========================================
TARGETS = [
    {"name": "nidaye", "url": "https://g4f.gg/nidaye"}
]

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

def send_unified_tg(results):
    if TG_TOKEN and TG_CHAT:
        try:
            lines = ["🤖 G4F 续期综合汇报"]
            for res in results:
                lines.append("-----------------------")
                lines.append(f"节点: {res['name']}")
                lines.append(f"状态: {res['status']}")
                lines.append(f"剩余时间: {res['time']}")
            msg = "\n".join(lines)
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
            print("Telegram 综合通知发送成功。")
        except Exception as e:
            print(f"发送通知失败: {e}")

print("\n===== 开始执行 =====")

proxy_str = "socks5://127.0.0.1:40000"

task_results = []
print("初始化物理鼠标依赖...")
os.system("sudo apt-get update > /dev/null 2>&1")
os.system("sudo apt-get install -y xdotool > /dev/null 2>&1")

for target in TARGETS:
    name = target["name"]
    url = target["url"]
    print(f"\n开始处理节点: [{name}]")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with SB(uc=True, proxy=proxy_str, headless=False, window_size="1920,1080", browser="chrome") as sb:
                print(f"正在访问目标网址: {url}")
                sb.driver.set_window_position(0, 0)
                sb.open(url)
                sb.sleep(6)
                os.makedirs("screenshots", exist_ok=True)
                sb.save_screenshot(f"screenshots/{name}_1_page_loaded.png")

                print("点击续期按钮 (#vm-submit)...")
                try:
                    sb.click('#vm-submit', timeout=5)
                    print("续期按钮点击成功")
                except Exception as e:
                    print(f"续期按钮点击失败: {e}")
                    # 尝试 JS 点击
                    sb.execute_script("document.getElementById('vm-submit').click()")

                print("等待人机验证加载...")
                time.sleep(6)

                print("执行验证框区域点击 (4x4 网格)...")
                xs = [790, 810, 830, 850]
                ys = [540, 560, 580, 600]
                for y in ys:
                    for x in xs:
                        os.system(f"xdotool mousemove {x} {y} click 1")
                        time.sleep(0.1)

                print("点击完成，等待验证盾亮起绿勾 (10秒)...")
                time.sleep(10)

                print("执行中心垂直扫射，确保物理击中 [VOTE] 按钮 (#sd-vote-btn)...")
                for sweep_y in range(600, 780, 30):
                    os.system(f"xdotool mousemove 960 {sweep_y} click 1")
                    time.sleep(0.2)

                print("等待 45 秒")
                time.sleep(45)

                print("奖励已发放，强制刷新页面")
                sb.refresh_page()
                sb.sleep(10)

                # 检查浏览器是否正常
                try:
                    _ = sb.driver.current_url
                except Exception as e:
                    print(f"浏览器连接已断开，尝试重新打开页面: {e}")
                    sb.open(url)
                    sb.sleep(10)

                print("获取剩余时间 (sp-timer-box)...")
                found_time = "未知"
                status = "❌ 续期失败"
                
                try:
                    # 尝试通过 CSS 选择器获取时间
                    timer_box = sb.wait_for_element('div.sp-timer-box', timeout=5)
                    found_time = timer_box.text.strip()
                    print(f"获取到时间: {found_time}")
                    
                    # 验证时间格式是否合理（应该包含数字）
                    if re.search(r'\d', found_time):
                        status = "✅ 续期成功"
                    else:
                        status = "⚠️ 状态未知"
                        
                except Exception as e:
                    print(f"获取 sp-timer-box 失败: {e}")
                    # 降级方案：通过 JS 获取
                    try:
                        found_time = sb.execute_script("""
                            const box = document.querySelector('div.sp-timer-box');
                            return box ? box.textContent.trim() : '未找到';
                        """)
                        print(f"JS 获取到时间: {found_time}")
                        
                        if found_time and found_time != '未找到' and re.search(r'\d', found_time):
                            status = "✅ 续期成功"
                        else:
                            status = "❌ 续期失败"
                    except Exception as e2:
                        print(f"JS 获取也失败: {e2}")

                print(f"最终结果: 状态={status}, 剩余时间={found_time}")

                try:
                    sb.save_screenshot(f"screenshots/{name}_2_result.png")
                except:
                    pass

                task_results.append({"name": name, "status": status, "time": found_time})
                break  # 成功则跳出重试循环

        except Exception as e:
            print(f"节点 [{name}] 第 {attempt+1} 次执行异常: {e}")
            if attempt < max_retries - 1:
                print(f"等待 10 秒后重试...")
                time.sleep(10)
            else:
                print(f"节点 [{name}] 重试次数用尽，标记为失败")
                task_results.append({"name": name, "status": "❌ 执行失败", "time": "未知"})

print("\n所有节点处理完毕，正在统一发送综合汇报...")
send_unified_tg(task_results)
