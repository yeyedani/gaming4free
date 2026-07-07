import os
import time
import json
import re
import urllib.request
from seleniumbase import SB

# ==========================================
# 💡 G4F.GG 自动续期 (纯原生 DOM 穿透 + 双重校验版)
# ==========================================

# 您的目标服务器配置
TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
]

# 从 GitHub Secrets 读取 Telegram 配置
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

def time_to_seconds(t_str):
    """将时分秒字符串转换为秒数，用于数学计算"""
    try:
        parts = t_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

def send_telegram_msg(results):
    """发送 Telegram 汇报"""
    if not (TG_TOKEN and TG_CHAT):
        print("未配置 TG_TOKEN 或 TG_CHAT_ID，跳过通知。")
        return
    try:
        lines = ["🤖 G4F 自动续期汇报"]
        for res in results:
            lines.append("-----------------------")
            lines.append(f"节点: {res['name']}")
            lines.append(f"状态: {res['status']}")
            lines.append(f"最新剩余时间: {res['time']}")
        msg = "\n".join(lines)
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
        print("Telegram 通知发送成功。")
    except Exception as e:
        print(f"Telegram 通知发送失败: {e}")

def main():
    print("\n===== 🚀 启动 G4F 自动续期任务 =====")
    task_results = []
    
    # 代理配置 (如果您的环境不需要代理，可以将此变量设为 None)
    proxy_str = "socks5://127.0.0.1:40000" if os.environ.get("USE_PROXY") else None

    for target in TARGETS:
        name = target["name"]
        url = target["url"]
        print(f"\n[{name}] 开始处理节点...")
        
        max_retries = 3
        found_time = "未知"
        status = "❌ 执行异常"
        
        for attempt in range(max_retries):
            print(f"[{name}] -> 正在进行第 {attempt + 1} 次尝试...")
            try:
                # uc=True 开启指纹伪装，uc_cdp=True 增强底层反爬穿透
                with SB(uc=True, uc_cdp=True, proxy=proxy_str, headless=False, window_size="1920,1080", browser="chrome") as sb:
                    sb.open(url)
                    sb.sleep(8)
                    
                    # 创建截图目录用于 Debug
                    os.makedirs("screenshots", exist_ok=True)
                    sb.save_screenshot(f"screenshots/{name}_1_loaded.png")

                    # --- 阶段 0：前置状态与初始时间记录 ---
                    if sb.is_element_visible('#sd-vote-btn'):
                        btn_text = sb.get_text('#sd-vote-btn').upper()
                        if 'WAIT' in btn_text:
                            status, found_time = "⏳ 处于冷却期", "不适用"
                            print(f"[{name}] 🛑 节点处于冷却期，跳过执行。")
                            break
                        elif 'VOTED' in btn_text:
                            status, found_time = "✅ 刚刚已投票", "不适用"
                            print(f"[{name}] ✅ 节点显示已投票，跳过执行。")
                            break

                    initial_sec = 0
                    if sb.is_element_visible('#sd-timer'):
                        initial_time_str = sb.get_text('#sd-timer').strip()
                        initial_sec = time_to_seconds(initial_time_str)
                        print(f"[{name}] 记录初始时间: {initial_time_str}")

                    # --- 阶段 1：唤醒投票弹窗 ---
                    print(f"[{name}] 触发主按钮 (#sd-vote-btn)...")
                    sb.execute_script("var b = document.getElementById('sd-vote-btn'); if(b) b.click();")

                    # 等待弹窗出现，最高容忍 45 秒广告时间
                    try:
                        sb.wait_for_element_visible('#vm-submit', timeout=45)
                    except:
                        raise Exception("弹窗加载超时，可能被广告卡死。")

                    # --- 阶段 2：静默等待 Cloudflare Token ---
                    print(f"[{name}] 监听 Cloudflare 验证状态...")
                    cf_passed = False
                    for i in range(30):
                        if sb.is_element_visible('#vm-submit'):
                            # 当 disabled 属性消失，说明 CF 返回了安全 token
                            if sb.get_attribute('#vm-submit', 'disabled') is None:
                                print(f"[{name}] -> CF 验证通过，按钮自然解锁！")
                                cf_passed = True
                                break
                        
                        # 超时辅助：如果 15 秒后还没解开，尝试用原生原生点击激活一下盾牌
                        if i == 15 and sb.is_element_visible('div.cf-turnstile iframe'):
                            print(f"[{name}] -> 尝试原生辅助激活验证盾...")
                            try:
                                sb.click('div.cf-turnstile iframe')
                            except:
                                pass
                        time.sleep(1)

                    if not cf_passed:
                        raise Exception("CF 验证未通过，缺少安全 Token。")

                    # --- 阶段 3：执行合法提交 ---
                    print(f"[{name}] 执行最终提交 (#vm-submit)...")
                    sb.execute_script("var b = document.getElementById('vm-submit'); if(b){ b.disabled=false; b.click(); }")
                    
                    # 侦听 API 返回的消息
                    for _ in range(10):
                        if sb.is_element_visible('#vm-msg'):
                            api_msg = sb.get_text('#vm-msg').strip().lower()
                            if api_msg and "submitting" not in api_msg:
                                print(f"[{name}] -> 底层接口反馈: {api_msg}")
                                break
                        time.sleep(1)

                    # --- 阶段 4：双重交叉验证 ---
                    print(f"[{name}] 刷新页面，执行双重交叉校验...")
                    sb.refresh_page()
                    sb.sleep(10)
                    
                    # 校验 A：时间差
                    new_sec = 0
                    if sb.is_element_visible('#sd-timer'):
                        found_time = sb.get_text('#sd-timer').strip()
                        new_sec = time_to_seconds(found_time)
                    time_diff = new_sec - initial_sec
                    
                    # 校验 B：最新流水账
                    recent_vote = ""
                    if sb.is_element_visible('.sp-vote-row .sp-vote-time'):
                        recent_vote = sb.get_text('.sp-vote-row .sp-vote-time').strip().lower()

                    print(f"[{name}] -> 最新时间: {found_time} (差值: {time_diff} 秒)")
                    print(f"[{name}] -> 最新流水账: {recent_vote}")

                    # 判定：时间增加 > 3000秒，或者流水账出现几秒/几分钟前
                    is_time_increased = time_diff > 3000
                    is_just_voted = any(x in recent_vote for x in ['sec', 'just', '0m', '1m', '2m', '3m'])

                    if is_time_increased or is_just_voted:
                        status = "✅ 续期成功"
                    else:
                        status = f"❌ 续期失败 (流水未更新)"

                    try:
                        sb.save_screenshot(f"screenshots/{name}_2_result.png")
                    except:
                        pass
                    
                    # 成功则立刻跳出重试循环
                    if "✅" in status:
                        break 

            except Exception as e:
                print(f"[{name}] 尝试异常: {e}")
                if attempt < max_retries - 1:
                    print("等待 10 秒后重试...\n")
                    time.sleep(10)
                else:
                    status = "❌ 执行彻底失败"

        task_results.append({"name": name, "status": status, "time": found_time})

    print("\n所有节点处理完毕，正在发送汇报...")
    send_telegram_msg(task_results)

if __name__ == "__main__":
    main()
