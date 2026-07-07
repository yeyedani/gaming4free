import os, time, urllib.request, json, re
from seleniumbase import SB

# ==========================================
# 💡 G4F.GG 自动续期 (V19 逻辑穿透版)
# ==========================================
TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
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

for target in TARGETS:
    name = target["name"]
    url = target["url"]
    print(f"\n开始处理节点: [{name}]")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 开启 uc_cdp=True，这是对抗 Cloudflare 的终极利器
            with SB(uc=True, uc_cdp=True, proxy=proxy_str, headless=False, window_size="1920,1080", browser="chrome") as sb:
                print(f"正在访问目标网址: {url}")
                sb.open(url)
                sb.sleep(8)
                os.makedirs("screenshots", exist_ok=True)
                sb.save_screenshot(f"screenshots/{name}_1_page_loaded.png")

                # --- 步骤 1：点击主界面的初始按钮 ---
                print("1. 点击初始续期按钮 (#sd-vote-btn)...")
                sb.execute_script("""
                    const btn = document.getElementById('sd-vote-btn');
                    if(btn) btn.click();
                """)
                sb.sleep(5)

                # --- 步骤 2：智能等待 CF 验证盾通过 ---
                print("2. 等待人机验证处理...")
                for _ in range(15):
                    # 检查确认按钮是否已经被 CF 解锁
                    is_unlocked = sb.execute_script("""
                        const submitBtn = document.getElementById('vm-submit');
                        return submitBtn && submitBtn.disabled === false;
                    """)
                    if is_unlocked:
                        print("验证已通过，按钮已解锁！")
                        break
                    time.sleep(1)

                # --- 步骤 3：DOM 穿透，强行点击最终确认 ---
                print("3. 注入提交指令 (#vm-submit)...")
                sb.execute_script("""
                    const submitBtn = document.getElementById('vm-submit');
                    if (submitBtn) {
                        submitBtn.disabled = false; // 强行解除任何可能的锁定
                        submitBtn.click();
                    }
                """)
                
                print("等待 15 秒确保 API 提交完成...")
                sb.sleep(15)

                # --- 步骤 4：刷新并提取最终时间 ---
                print("4. 强制刷新页面提取最新时间...")
                sb.refresh_page()
                sb.sleep(8)

                found_time = "未知"
                status = "❌ 续期失败"
                
                # 直接通过具体的 ID 获取时间，比获取整个 div.sp-timer-box 更精确
                try:
                    found_time = sb.execute_script("return document.getElementById('sd-timer') ? document.getElementById('sd-timer').innerText : '未知';")
                    print(f"精确获取到时间: {found_time}")
                    
                    if found_time and found_time != '未知' and re.search(r'\d', found_time):
                        status = "✅ 续期成功"
                    else:
                        # 备用方案：读取全文判断是否包含 +90m 等成功字样
                        page_text = sb.get_text("body").upper()
                        if "VOTED" in page_text or "90 MIN" in page_text:
                            status = "✅ 续期成功 (基于文本模糊匹配)"
                            
                except Exception as e:
                    print(f"获取时间失败: {e}")

                print(f"最终结果: 状态={status}, 剩余时间={found_time}")
                try:
                    sb.save_screenshot(f"screenshots/{name}_2_result.png")
                except:
                    pass

                task_results.append({"name": name, "status": status, "time": found_time})
                
                # 如果成功，立刻跳出重试循环
                if "成功" in status:
                    break 

        except Exception as e:
            print(f"节点 [{name}] 第 {attempt+1} 次执行异常: {e}")
            if attempt < max_retries - 1:
                print("等待 10 秒后重试...")
                time.sleep(10)
            else:
                print(f"节点 [{name}] 重试次数用尽，标记为失败")
                task_results.append({"name": name, "status": "❌ 执行异常", "time": "未知"})

print("\n所有节点处理完毕，正在统一发送综合汇报...")
send_unified_tg(task_results)
