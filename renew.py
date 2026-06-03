import os, sys, time, urllib.request, json
from seleniumbase import SB

# ==========================================
# 💡 核心配置 (G4F.GG 终极雷达制导防弹版)
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

print(f"\n===== 🚀 开始执行极速续期 (终极雷达制导狙击版 v2) =====")

proxy_str = "socks5://127.0.0.1:40000"

with SB(uc=True, proxy=proxy_str, headless=False, window_size="1920,1080") as sb:
    try:
        print("⏳ 正在为虚拟显示器安装 xdotool 物理鼠标引擎...")
        os.system("sudo apt-get update > /dev/null 2>&1")
        os.system("sudo apt-get install -y xdotool > /dev/null 2>&1")

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

        print("🚀 触发 [+ ADD 90 MIN] 核心按钮...")
        # 🌟 修复 1：同样套上 IIFE 外壳，杜绝一切隐患
        js_click_code = """
        return (function() {
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
        })();
        """
        is_clicked = sb.execute_script(js_click_code)
        if not is_clicked:
            sb.click('xpath=//*[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "add 90")]')

        print("⏳ 盲等 6 秒钟，等待 CF 盾在屏幕上展开...")
        time.sleep(6) 
        
        print("🛡️ 启动【动态雷达追踪】模块，锁定靶心！")
        
        # 🌟 修复 2：使用标准 IIFE 函数包裹，彻底解决 V8 引擎的语法报错！
        js_radar = """
        return (function() {
            let cf = document.querySelector('iframe[src*="cloudflare"], iframe[src*="turnstile"], iframe[title*="Cloudflare"]');
            // 没有盾直接返回空，这里在函数内 return 绝对合法
            if (!cf) return ""; 
            
            let rect = cf.getBoundingClientRect();
            
            // 虚拟浏览器标准顶部导航栏高度约为 85px
            let ui_y = 85; 
            
            // 计算靶心：向右偏 30px (复选框位置)，加上高度的一半
            let target_x = rect.left + 30;
            let target_y = rect.top + ui_y + (rect.height / 2);
            
            return Math.round(target_x) + "," + Math.round(target_y);
        })();
        """
        
        coords = sb.execute_script(js_radar)
        
        if coords:
            target_x, target_y = coords.split(",")
            print(f"🎯 雷达精确锁定 CF 盾绝对靶心: ({target_x}, {target_y})")
            print("🖱️ 物理鼠标按下扳机！")
            
            # 使用算出的绝对坐标，让物理鼠标去点！
            os.system(f"xdotool mousemove {target_x} {target_y} click 1")
            
            print("⏳ 射击完毕！静默等待 8 秒，让子弹飞一会儿 (等待盾转圈通过)...")
            time.sleep(8)
        else:
            print("⏩ 雷达未扫描到 CF 盾，可能已自动放行。")
            
        try:
            sb.save_screenshot("screenshots/2_result.png")
            print("📸 最终战况截图已保存。")
        except:
            print("⚠️ 截图保存失败。")

        print("✅ 流程执行完毕！")
        send_tg(f"✅ 服务器 [{MC_USERNAME}] 续期脚本运行完毕！\n【破盾方式: 动态雷达制导物理盲狙】请查阅 GitHub 截图确认战果。")

    except Exception as e:
        print(f"❌ 发生致命错误: {e}")
        try:
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot("screenshots/error.png")
        except:
            pass
        send_tg(f"❌ 自动续期崩溃: {e}")
