import os, sys, time, urllib.request, json
from seleniumbase import SB
from selenium.webdriver.common.action_chains import ActionChains

# ==========================================
# 💡 核心配置 (适配全新 g4f.gg 界面)
# ==========================================
TARGET_URL = "https://g4f.gg/renqi" 
MC_USERNAME = "renqi"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")

def send_tg(msg):
    if TG_TOKEN and TG_CHAT:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": TG_CHAT, "text": f"🤖 G4F 自动续期:\n{msg}"}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=10)
        except:
            pass

print(f"\n===== 🚀 开始执行极速续期 (G4F.GG 赛博朋克全新版) =====")

proxy_str = "socks5://127.0.0.1:40000"

with SB(uc=True, proxy=proxy_str, headless=False) as sb:
    try:
        print(f"🌐 正在通过 WARP 访问新版目标网址: {TARGET_URL}")
        sb.open(TARGET_URL)
        
        sb.sleep(6) 
        
        os.makedirs("screenshots", exist_ok=True)
        sb.save_screenshot("screenshots/1_page_loaded.png")

        print("✍️ 尝试填入游戏ID (OPTIONAL)...")
        try:
            sb.type('input[placeholder*="Steve"], input[placeholder*="Player"]', MC_USERNAME, timeout=4)
            print("✅ ID 填入成功！")
        except:
            print("ℹ️ 未找到输入框或无需填入，继续下一步。")

        print("🚀 寻找 [+ ADD 90 MIN] 核心按钮并执行降维打击...")
        
        js_click_code = """
        let clicked = false;
        let els = document.querySelectorAll('button, a, input, div, span');
        for (let i = els.length - 1; i >= 0; i--) {
            let el = els[i];
            let text = (el.innerText || el.value || '').toUpperCase();
            if (text.includes('ADD 90')) {
                el.click();
                clicked = true;
                break;
            }
        }
        return clicked;
        """
        
        is_clicked = sb.execute_script(js_click_code)
        
        if is_clicked:
            print("🖱️ JavaScript 强制穿透点击成功！")
        else:
            print("⚠️ JS 未能点击，尝试备用 XPath 方案...")
            sb.click('xpath=//*[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "add 90")]')

        print("⏳ 盲等 6 秒钟，让 CF 盾在静默中完全加载 (严禁探测)...")
        time.sleep(6) 
        
        try:
            print("🛡️ 启动【隔山打牛】物理盲狙模式，绝不进入危险框架！")
            
            # 🌟 核心杀手锏：在主页面上，直接找到 CF 盾的外壳 (iframe 元素本身)
            iframe_xpath = '//iframe[contains(@src, "cloudflare") or contains(@src, "turnstile") or contains(@title, "Cloudflare")]'
            cf_iframe = sb.driver.find_element("xpath", iframe_xpath)
            
            # 🌟 调取原生鼠标动作链，瞄准 iframe 外壳的正中心，直接扣动扳机！
            # 因为我们没有 switch_to_frame，CF 根本察觉不到有机器人在试图控制它！
            ActionChains(sb.driver).move_to_element(cf_iframe).click().perform()
            
            print("🖱️ 已从外部成功狙击 CF 盾！等待验证转圈...")
            time.sleep(6)
            
        except Exception as e:
            print(f"⏩ 狙击模块跳过 (未找到盾或已被自动放行): {e}")

        print("⏳ 等待最终续期结果加载 (等待 6 秒)...")
        time.sleep(6)
        
        try:
            sb.save_screenshot("screenshots/2_result.png")
        except:
            print("⚠️ 截图保存失败。")

        print("✅ 流程执行完毕！")
        send_tg(f"✅ 服务器 [{MC_USERNAME}] 续期脚本运行完毕！\n请查阅 GitHub 最新截图确认 CF 盾是否通过以及时间是否增加。")

    except Exception as e:
        print(f"❌ 发生致命错误: {e}")
        try:
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot("screenshots/error.png")
        except:
            pass
        send_tg(f"❌ 自动续期崩溃: {e}")
