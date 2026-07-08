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

                # ================== 核心修正 1：死等主页面 CF 盾 ==================
                self.log("🛡️ 等待主页面彻底加载完毕...")
                try:
                    # 强制等待核心投票按钮出现。如果被 CF 卡住，uc 会自动处理，我们只需耐心等
                    sb.wait_for_element('#sd-vote-btn', timeout=30)
                except Exception:
                    self.log("⚠️ 遇到顽固大盾，尝试点击验证码中心...")
                    try:
                        if sb.is_element_visible('input[type="checkbox"]'):
                            sb.click('input[type="checkbox"]')
                        elif sb.is_element_visible('div.cf-turnstile iframe'):
                            sb.click('div.cf-turnstile iframe')
                        sb.wait_for_element('#sd-vote-btn', timeout=20)
                    except:
                        raise Exception("主页面被 Cloudflare 彻底拦截，未能加载。")

                # ================== 获取初始时间与状态 ==================
                btn_text = sb.get_text('#sd-vote-btn').upper()
                if 'WAIT' in btn_text:
                    self.log("🛑 节点处于冷却期，跳过执行。")
                    self.task_results.append({"name": region, "status": "⏳ 冷却中", "time": "不适用"})
                    return
                elif 'VOTED' in btn_text:
                    self.log("✅ 节点显示已投票，跳过执行。")
                    self.task_results.append({"name": region, "status": "✅ 已投票", "time": "不适用"})
                    return

                initial_time_str = "00:00:00"
                if sb.is_element_visible('#sd-timer'):
                    initial_time_str = sb.get_text('#sd-timer').strip()
                initial_sec = time_to_seconds(initial_time_str)
                self.log(f"🕒 初始真实时间: {initial_time_str} ({initial_sec} 秒)")

                # ================== 核心修正 2：击杀广告进程 ==================
                self.log("🖱️ 破坏广告环境，强开投票弹窗...")
                # 将全局广告队列设为 null，让网页误以为广告失败，从而直接弹窗！
                sb.execute_script("window.ramp = null;")
                sb.execute_script("var b = document.getElementById('sd-vote-btn'); if(b) b.click();")
                
                try:
                    # 去掉了广告，弹窗会瞬间出现，等 15 秒足矣
                    sb.wait_for_element_visible('#vm-submit', timeout=15)
                except:
                    raise Exception("杀广告后弹窗仍未出现，网页结构可能发生重大变更。")

                # ================== 等待弹窗内的 CF 验证 ==================
                self.log("🛡️ 开始迎战弹窗 Cloudflare 验证...")
                cf_passed = False
                
                for i in range(35):
                    # 自然解锁检测
                    is_unlocked = sb.execute_script("return document.getElementById('vm-submit').disabled === false;")
                    if is_unlocked:
                        self.log("✅ Cloudflare 验证通过，拿到安全 Token！")
                        cf_passed = True
                        break
                    
                    # 辅助点击检测
                    if i > 0 and i % 5 == 0:
                        try:
                            if sb.is_element_visible("div.cf-turnstile iframe"):
                                self.log("⚠️ 尝试辅助点击 CF 验证框...")
                                sb.click_if_visible("div.cf-turnstile iframe")
                        except:
                            pass
                    time.sleep(1)

                if not cf_passed:
                    raise Exception("弹窗内 Cloudflare 验证未能解开，缺少 Token 无法提交。")

                # ================== 最终提交与验证 ==================
                self.log("🖱️ 执行合法提交...")
                sb.click('#vm-submit')
                
                self.log("⏳ 等待接口反馈...")
                server_msg = ""
                for _ in range(15):
                    if sb.is_element_visible('#vm-msg'):
                        msg = sb.get_text('#vm-msg').strip().lower()
                        if msg and "submitting" not in msg:
                            server_msg = msg
                            self.log(f"💬 服务器提示: {server_msg}")
                            break
                    time.sleep(1)

                self.log("⏳ 页面数据同步中...")
                time.sleep(15)
                sb.refresh_page()
                time.sleep(10)

                # ================== 数学交叉验证 ==================
                timestamp_after = "00:00:00"
                if sb.is_element_visible('#sd-timer'):
                    timestamp_after = sb.get_text('#sd-timer').strip()
                new_sec = time_to_seconds(timestamp_after)
                time_diff = new_sec - initial_sec

                recent_vote = ""
                if sb.is_element_visible('.sp-vote-row .sp-vote-time'):
                    recent_vote = sb.get_text('.sp-vote-row .sp-vote-time').strip().lower()

                self.log(f"🕒 更新后时间: {timestamp_after} (秒数差值: {time_diff} 秒)")
                self.log(f"📝 最新流水账: {recent_vote}")

                is_time_increased = time_diff > 3000
                is_just_voted = any(x in recent_vote for x in ['sec', 'just', '0m', '1m', '2m', '3m'])

                if is_time_increased or is_just_voted:
                    status = "✅ 成功续期"
                    self.log("🎉 验证无误，续期成功！")
                else:
                    status = "❌ 失败 (流水未变)"
                    self.log(f"💔 失败原因：时间与流水账均未刷新。")
                
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
