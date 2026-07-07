import os, time, urllib.request, json, re
from seleniumbase import SB

# ==========================================
# 💡 G4F.GG 自动续期 (DOM 级精准绝杀版)
# ==========================================
TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
]

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

def send_unified_tg(results):
    if not (TG_TOKEN and TG_CHAT): return
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
        print("Telegram 通知发送成功。")
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
    found_time = "未知"
    status = "❌ 执行异常"
    
    for attempt in range(max_retries):
        print(f"-> 正在进行第 {attempt + 1} 次尝试...")
        try:
            # 启用 uc_cdp=True 以获得最强 Cloudflare 绕过能力
            with SB(uc=True, uc_cdp=True, proxy=proxy_str, headless=False, window_size="1920,1080", browser="chrome") as sb:
                print(f"正在访问目标网址: {url}")
                sb.open(url)
                sb.sleep(8)
                
                os.makedirs("screenshots", exist_ok=True)
                sb.save_screenshot(f"screenshots/{name}_1_page_loaded.png")

                # --- 步骤 1：精确触发主按钮 ---
                print("1. 触发主页续期按钮 (#sd-vote-btn)...")
                sb.execute_script("document.getElementById('sd-vote-btn') && document.getElementById('sd-vote-btn').click();")
                sb.sleep(5)

                # --- 步骤 2：智能等盾 ---
                print("2. 监听 Cloudflare 验证状态...")
                for _ in range(20):
                    # 严谨校验：确保 vm-submit 存在，且 disabled 属性已被 CF 移除
                    is_ready = sb.execute_script("return document.getElementById('vm-submit') !== null && document.getElementById('vm-submit').disabled === false;")
                    if is_ready:
                        print("-> CF 验证已通过，按钮锁已解开！")
                        break
                    time.sleep(1)

                # --- 步骤 3：底层穿透提交 ---
                print("3. 执行 DOM 级强制提交 (#vm-submit)...")
                sb.execute_script("""
                    {
                        let submitBtn = document.getElementById('vm-submit');
                        if (submitBtn) {
                            submitBtn.disabled = false; // 强行开锁，双重保险
                            submitBtn.click();
                        }
                    }
                """)
                
                # --- 步骤 4：即时回执校验 (利用截图里的 #vm-msg) ---
                print("等待 10 秒 API 响应...")
                sb.sleep(10)
                msg_text = sb.execute_script("return document.getElementById('vm-msg') ? document.getElementById('vm-msg').innerText : '';")
                print(f"弹窗底层反馈: {msg_text}")

                # --- 步骤 5：刷新页面，提取最终时钟 ---
                print("4. 刷新页面，提取最终剩余时间 (#sd-timer)...")
                sb.refresh_page()
                sb.sleep(8)
                
                try:
                    # 极其精确地提取时间文本
                    found_time = sb.execute_script("return document.getElementById('sd-timer') ? document.getElementById('sd-timer').innerText.trim() : '未知';")
                    print(f"精确提取到倒计时: {found_time}")
                    
                    if found_time and found_time != '未知' and re.search(r'\d', found_time):
                        status = "✅ 续期成功"
                    else:
                        page_text = sb.get_text("body").upper()
                        if "VOTED" in page_text or "90 MIN" in page_text:
                            status = "✅ 续期成功 (基于全局文本判定)"
                        else:
                            status = "❌ 续期失败"
                except Exception as e:
                    print(f"提取计时器失败: {e}")

                print(f"当前节点最终结果: 状态={status}, 剩余时间={found_time}")
                try:
                    sb.save_screenshot(f"screenshots/{name}_2_result.png")
                except:
                    pass
                
                if "成功" in status:
                    break 

        except Exception as e:
            print(f"节点 [{name}] 第 {attempt+1} 次执行出现异常: {e}")
            if attempt < max_retries - 1:
                print("等待 10 秒后准备重试...")
                time.sleep(10)
            else:
                print(f"节点 [{name}] 机会用尽。")
                status = "❌ 执行彻底失败"

    task_results.append({"name": name, "status": status, "time": found_time})

print("\n所有节点处理完毕，正在发送汇报...")
send_unified_tg(task_results)
