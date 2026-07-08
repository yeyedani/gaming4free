import time
import os
import json
import random
import urllib.request

# ================= 智能环境配置 =================
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"
if "XAUTHORITY" not in os.environ:
    if os.path.exists("/home/headless/.Xauthority"):
        os.environ["XAUTHORITY"] = "/home/headless/.Xauthority"

from seleniumbase import SB

# ================= 核心参数配置 =================
PROXY_URL = "socks5://127.0.0.1:10808"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")

# 替换为您需要续期的目标
TARGETS = [
    {"num": "nidaye", "region": "nidaye"}
]

def time_to_seconds(t_str):
    """将倒计时转换为纯秒数，用于绝对精准的数学计算"""
    try:
        parts = t_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

class Game4FreeRenewal:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.screenshot_dir = os.path.join(self.BASE_DIR, "screenshots")
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        self.task_results = []

    def log(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] [INFO] {msg}", flush=True)

    def send_telegram_notify(self):
        if not TG_TOKEN or not TG_CHAT_ID:
            self.log("⚠️ 未配置 TG_TOKEN 或 TG_CHAT_ID，跳过推送。")
            return
        try:
            lines = ["🤖 G4F 续期综合汇报"]
            for res in self.task_results:
                lines.append("-----------------------")
                lines.append(f"节点: {res['name']}")
                lines.append(f"状态: {res['status']}")
                lines.append(f"剩余时间: {res['time']}")
            
            msg = "\n".join(lines)
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TG_CHAT_ID, "text": msg}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
            self.log("✅ TG 综合推送已发送")
        except Exception as e:
            self.log(f"❌ TG 推送失败: {e}")

    def run_single_server(self, server_num, region):
        URL_APP_PANEL = f"https://g4f.gg/{server_num}"
        
        self.log("=" * 40)
        self.log(f"🚀 开始处理节点 [{region}]")
        self.log("=" * 40)

        with SB(
            uc=True,
            uc_cdp=True,
            headless=False,
            chromium_arg="--no-sandbox,--disable-dev-shm-usage,--disable-gpu,--window-position=0,0,--start-maximized",
            proxy=PROXY_URL
        ) as sb:
            try:
                self.log(f"📂 正在访问目标网址...")
                sb.uc_open_with_reconnect(URL_APP_PANEL, reconnect_time=5)
                time.sleep(8)

                # ================== 获取初始时间 ==================
                initial_time_str = "00:00:00"
                if sb.is_element_visible('#sd-timer'):
                    initial_time_str = sb.get_text('#sd-timer').strip()
                initial_sec = time_to_seconds(initial_time_str)
                self.log(f"🕒 初始真实时间: {initial_time_str} ({initial_sec} 秒)")

                # ================== 点击主按钮 ==================
                self.log("🖱️ 唤醒投票弹窗...")
                sb.execute_script("var b = document.getElementById('sd-vote-btn'); if(b) b.click();")
                
                try:
                    sb.wait_for_element_visible('#vm-submit', timeout=45)
                except:
                    raise Exception("未找到投票弹窗，可能被广告完全拦截。")

                # ================== 【核心修复】真实破盾逻辑 ==================
                self.log("🛡️ 开始迎战 Cloudflare 盾牌...")
                cf_passed = False
                
                # 轮询长达 40 秒，绝不强行撬锁，死等 Token 下发
                for i in range(40):
                    # 检查自然解锁：网页 JS 拿到 Token 后，会自动移除 disabled 属性
                    is_unlocked = sb.execute_script("return document.getElementById('vm-submit').disabled === false;")
                    if is_unlocked:
                        self.log("✅ Cloudflare 验证真实通过，拿到安全 Token！")
                        cf_passed = True
                        break
                    
                    # 每隔 6 秒，尝试物理点击一次验证框区域，刺激盾牌弹绿勾
                    if i > 0 and i % 6 == 0:
                        try:
                            if sb.is_element_visible("div.cf-turnstile iframe"):
                                self.log("⚠️ 尝试辅助点击 CF 验证框...")
                                sb.click_if_visible("div.cf-turnstile iframe")
                        except:
                            pass
                    time.sleep(1)

                if not cf_passed:
                    raise Exception("Cloudflare 验证始终未能解开，强行提交必败，放弃当前操作。")

                # ================== 最终提交与接口抓取 ==================
                self.log("🖱️ 执行合法提交...")
                sb.click('#vm-submit')
                
                self.log("⏳ 等待后端接口真实反馈...")
                server_msg = ""
                for _ in range(15):
                    if sb.is_element_visible('#vm-msg'):
                        msg = sb.get_text('#vm-msg').strip().lower()
                        if msg and "submitting" not in msg:
                            server_msg = msg
                            self.log(f"💬 服务器提示: {server_msg}")
                            break
                    time.sleep(1)

                self.log("⏳ 等待 15 秒页面数据同步...")
                time.sleep(15)
                sb.refresh_page()
                time.sleep(10)

                # ================== 【核心修复】数学级时间校验 ==================
                timestamp_after = "00:00:00"
                if sb.is_element_visible('#sd-timer'):
                    timestamp_after = sb.get_text('#sd-timer').strip()
                new_sec = time_to_seconds(timestamp_after)
                
                time_diff = new_sec - initial_sec
                self.log(f"🕒 更新后时间: {timestamp_after} (秒数差值: {time_diff} 秒)")

                # 判断逻辑：只要时间比原来多出了 3000 秒以上（正常是加 5400 秒），才是真成功
                if time_diff > 3000:
                    status = "✅ 成功续期"
                    self.log("🎉 验证无误，时间确实增加了！")
                else:
                    status = "❌ 失败 (时间未涨)"
                    self.log(f"💔 失败原因：时间仅变动 {time_diff} 秒，接口极可能拦截了请求。")
                
                try:
                    sb.save_screenshot(f"{self.screenshot_dir}/{region}_final_result.png")
                except:
                    pass

                self.task_results.append({"name": region, "status": status, "time": timestamp_after})

            except Exception as e:
                self.log(f"❌ 运行异常: {e}")
                try:
                    sb.save_screenshot(f"{self.screenshot_dir}/{region}_exception.png")
                except:
                    pass
                self.task_results.append({"name": region, "status": "❌ 异常崩溃", "time": "未知"})

    def run(self):
        for target in TARGETS:
            max_retries = 3
            for attempt in range(max_retries):
                prev_len = len(self.task_results)
                self.run_single_server(target["num"], target["region"])
                
                if len(self.task_results) > prev_len:
                    last_status = self.task_results[-1]["status"]
                    if "✅" in last_status or "⏳" in last_status:
                        break
                    elif attempt < max_retries - 1:
                        self.log(f"⚠️ 节点 {target['region']} 操作失败，等待 15 秒后进行第 {attempt + 2} 次重试...\n")
                        self.task_results.pop()
                        time.sleep(15)
        
        self.log("\n所有节点处理完毕，开始发送通知...")
        self.send_telegram_notify()

if __name__ == "__main__":
    Game4FreeRenewal().run()
