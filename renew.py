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
    try:
        with SB(uc=True, proxy=proxy_str, headless=False, window_size="1920,1080") as sb:
            print(f"正在访问目标网址: {url}")
            sb.driver.set_window_position(0, 0)
            sb.open(url)
            sb.sleep(6)
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot(f"screenshots/{name}_1_page_loaded.png")

            print("点击初始续期按钮...")
            js_click_code = """
let step1_els = document.querySelectorAll('button, a, input, div, span');
for (let i = step1_els.length - 1; i >= 0; i--) {
    let el = step1_els[i];
    let text = (el.innerText || el.value || '').toUpperCase();
    if (text.includes('ADD 90')) {
        el.click();
        break;
    }
}
"""
            sb.execute_script(js_click_code)
            try:
                sb.click('xpath=//*[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "add 90")]', timeout=2)
            except:
                pass

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

            print("执行中心垂直扫射，确保物理击中 [VOTE] 按钮...")
            for sweep_y in range(600, 780, 30):
                os.system(f"xdotool mousemove 960 {sweep_y} click 1")
                time.sleep(0.2)

            print("等待 45 秒")
            time.sleep(45)

            print("奖励已发放，强制刷新页面")
            sb.refresh_page()
            time.sleep(8)  # 等待新页面加载完毕

            # ========== 修复部分 ==========
            print("获取页面完整 HTML 内容...")
            page_html = sb.driver.page_source
            
            # 打印前 500 个字符用于调试
            print(f"页面内容开头: {page_html[:500]}")
            
            # 尝试匹配多种时间格式
            time_patterns = [
                r'(\d{2}:\d{2}:\d{2})',           # HH:MM:SS
                r'(\d+)\s*天\s*(\d+)\s*时',         # X天Y时
                r'(\d+)\s*小时',                     # X小时
                r'(\d+)\s*分钟',                     # X分钟
            ]
            
            found_time = "未知"
            found_status = False
            
            for pattern in time_patterns:
                match = re.search(pattern, page_html)
                if match:
                    found_time = match.group(0)
                    found_status = True
                    print(f"匹配到时间模式 [{pattern}]: {found_time}")
                    break
            
            # 额外检查：查找包含"剩余"、"剩余时间"、"expires"、"expiry"等关键词附近的文本
            if not found_status:
                expiry_keywords = ['剩余', '剩余时间', 'expires', 'expiry', 'expire', '有效期', 'valid']
                for keyword in expiry_keywords:
                    idx = page_html.find(keyword)
                    if idx != -1:
                        # 提取关键词前后 100 个字符
                        context = page_html[max(0, idx-50):idx+150]
                        print(f"找到关键词 '{keyword}' 上下文: {context}")
                        time_match = re.search(r'(\d{2}:\d{2}:\d{2}|\d+\s*天\s*\d+\s*时|\d+\s*小时|\d+\s*分钟)', context)
                        if time_match:
                            found_time = time_match.group(1)
                            found_status = True
                            break
            
            # 判断续期是否真正成功
            # 检查页面上是否有"续期成功"、"已续期"、"success"、"renewed"等字样
            success_keywords = ['续期成功', '已续期', 'success', 'renewed', 'renewal success', '奖励已发放']
            success_found = False
            for kw in success_keywords:
                if kw.lower() in page_html.lower():
                    success_found = True
                    print(f"找到成功关键词: {kw}")
                    break
            
            # 最终判断逻辑
            if found_status and found_time != "未知":
                status = "✅ 续期成功"
            elif success_found:
                status = "✅ 续期成功"
            else:
                status = "❌ 续期失败"
            
            print(f"最终结果: 状态={status}, 剩余时间={found_time}")
            # ========== 修复结束 ==========

            try:
                sb.save_screenshot(f"screenshots/{name}_2_result.png")
            except:
                pass

            task_results.append({"name": name, "status": status, "time": found_time})

    except Exception as e:
        print(f"节点 [{name}] 执行过程中发生异常: {e}")
        task_results.append({"name": name, "status": "❌ 执行失败", "time": "未知"})

print("\n所有节点处理完毕，正在统一发送综合汇报...")
send_unified_tg(task_results)
