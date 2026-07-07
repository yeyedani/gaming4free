import os, time, urllib.request, json, re
from seleniumbase import SB

# ==========================================
# 💡 G4F.GG 自动续期 (V22 流水账交叉验证版)
# ==========================================
TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
]

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

# 时间转秒数辅助函数
def time_to_seconds(t_str):
    try:
        parts = t_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    except:
        return 0

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
        print(f"\n-> 正在进行第 {attempt + 1} 次尝试...")
        try:
            with SB(uc=True, uc_cdp=True, proxy=proxy_str, headless=False, window_size="1920,1080", browser="chrome") as sb:
                print(f"正在访问目标网址: {url}")
                sb.open(url)
                sb.sleep(8)
                
                os.makedirs("screenshots", exist_ok=True)
                sb.save_screenshot(f"screenshots/{name}_1_page_loaded.png")

                # --- 步骤 0：记录初始时间与状态 ---
                btn_state = sb.execute_script("""
                    const btn = document.getElementById('sd-vote-btn');
                    if (!btn) return 'NOT_FOUND';
                    const txt = btn.innerText.toUpperCase();
                    if (txt.includes('WAIT')) return 'COOLDOWN';
                    if (txt.includes('VOTED')) return 'ALREADY_VOTED';
                    return 'READY';
                """)
                if btn_state == 'COOLDOWN':
                    status, found_time = "⏳ 冷却中 (未到时间)", "不适用"
                    print("🛑 节点处于冷却期，跳过执行。")
                    break
                elif btn_state == 'ALREADY_VOTED':
                    status, found_time = "✅ 刚刚已投票", "不适用"
                    print("✅ 节点显示已投票，跳过执行。")
                    break

                initial_time_str = sb.execute_script("return document.getElementById('sd-timer') ? document.getElementById('sd-timer').innerText.trim() : '00:00:00';")
                initial_sec = time_to_seconds(initial_time_str)
                print(f"0. 记录投票前初始时间: {initial_time_str} ({initial_sec} 秒)")

                # --- 步骤 1：触发主按钮 ---
                print("1. 触发主页续期按钮 (#sd-vote-btn)...")
                sb.execute_script("document.getElementById('sd-vote-btn') && document.getElementById('sd-vote-btn').click();")

                # --- 步骤 2：扛过广告，等弹窗 ---
                print("2. 等待广告结束及投票弹窗加载 (最长 45 秒)...")
                try:
                    sb.wait_for_element_visible('#vm-submit', timeout=45)
                except:
                    raise Exception("未能等出投票弹窗，可能被广告卡死。")

                # --- 步骤 3：动态获取坐标，物理激活验证盾 ---
                print("3. 监听 Cloudflare 验证状态...")
                cf_passed = False
                for i in range(25):
                    is_unlocked = sb.execute_script("return document.getElementById('vm-submit') !== null && document.getElementById('vm-submit').disabled === false;")
                    if is_unlocked:
                        print("   -> CF 验证成功，确认按钮自然解锁！")
                        cf_passed = True
                        break
                    
                    if i > 0 and i % 5 == 0:
                        cf_rect = sb.execute_script("""
                            let ts = document.querySelector('div.cf-turnstile iframe');
                            if (ts) {
                                let rect = ts.getBoundingClientRect();
                                return {x: rect.left + rect.width/2, y: rect.top + rect.height/2};
                            }
                            return null;
                        """)
                        if cf_rect:
                            base_x, base_y = int(cf_rect['x']), int(cf_rect['y'])
                            print(f"   -> 探测到验证盾动态坐标 (X={base_x}, Y={base_y})，辅助激活...")
                            for offset_y in [75, 90, 105]:
                                for offset_x in [-15, 0, 15]:
                                    os.system(f"xdotool mousemove {base_x + offset_x} {base_y + offset_y} click 1")
                                    time.sleep(0.05)
                    time.sleep(1)

                if not cf_passed:
                    raise Exception("Cloudflare 验证盾未能解开，无法获取安全 Token。")

                # --- 步骤 4：合法提交 ---
                print("4. 执行合法提交 (#vm-submit)...")
                sb.execute_script("document.getElementById('vm-submit').click();")
                
                print("等待 API 反馈...")
                api_msg = ""
                for _ in range(15):
                    api_msg = sb.execute_script("return document.getElementById('vm-msg') ? document.getElementById('vm-msg').innerText.trim() : '';")
                    if api_msg and "submitting" not in api_msg.lower():
                        break
                    time.sleep(1)
                print(f"   -> 底层弹窗反馈: {api_msg}")

                # --- 步骤 5：【核心】双重交叉校验（时间差 + 投票流水账） ---
                print("5. 强制刷新页面，执行双重交叉校验...")
                sb.refresh_page()
                sb.sleep(10)
                
                # 校验点 A：获取时钟
                new_time_str = sb.execute_script("return document.getElementById('sd-timer') ? document.getElementById('sd-timer').innerText.trim() : '00:00:00';")
                new_sec = time_to_seconds(new_time_str)
                time_diff = new_sec - initial_sec
                found_time = new_time_str
                
                # 校验点 B：嗅探最新投票记录
                recent_vote = sb.execute_script("""
                    let el = document.querySelector('.sp-vote-row .sp-vote-time');
                    return el ? el.innerText.trim().toLowerCase() : '';
                """)
                print(f"   -> 刷新后最新时间: {new_time_str} (差值: {time_diff} 秒)")
                print(f"   -> 最新投票流水账: {recent_vote}")

                # 判定逻辑：时间大涨 OR 最新流水账显示刚才有投票
                is_time_increased = time_diff > 3000
                is_just_voted = any(x in recent_vote for x in ['sec', 'just', '0m', '1m', '2m'])

                if is_time_increased or is_just_voted:
                    status = "✅ 续期成功 (校验通过)"
                else:
                    status = f"❌ 续期失败 (流水账: {recent_vote})"

                print(f"当前节点最终结果: 状态={status}, 剩余时间={found_time}")
                try:
                    sb.save_screenshot(f"screenshots/{name}_2_result.png")
                except:
                    pass
                
                if "✅" in status:
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
