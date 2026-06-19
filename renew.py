import os, time, subprocess, requests
from DrissionPage import ChromiumPage, ChromiumOptions

URL = "https://g4f.gg/nidaye"
TARGET_HOURS = 48
COOLDOWN_MINUTES = 31
MAX_LOOPS = 50

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_tg_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
    except: pass

def rotate_warp_ip(old_ip):
    for _ in range(3):
        subprocess.run(['warp-cli', '--accept-tos', 'disconnect'], stdout=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.run(['warp-cli', '--accept-tos', 'connect'], stdout=subprocess.DEVNULL)
        time.sleep(8) 
        try: new_ip = requests.get('https://api.ipify.org', timeout=5).text
        except: new_ip = "获取失败"
        if new_ip != "获取失败" and new_ip != old_ip: return new_ip
    return "获取失败"

def get_current_hours(time_text):
    try: return int(time_text.split(':')[0]) if time_text else -1
    except: return -1

def solve_turnstile(page):
    try:
        iframe = page.get_frame('css:iframe[src^="https://challenges.cloudflare.com"]', timeout=5)
        if not iframe: return False
        time.sleep(2)
        try: iframe.ele('tag:body').shadow_root.ele('css:input[type="checkbox"]').click.at(offset_x=10, offset_y=10)
        except: iframe.frame_ele.click.at(offset_x=30, offset_y=30)
        for _ in range(15):
            time.sleep(1)
            resp = page.ele('css:[name="cf-turnstile-response"]', timeout=1)
            if resp and len(resp.value) > 10: return True
        return False
    except: return False

def main():
    co = ChromiumOptions().auto_port()
    co.set_browser_path('/usr/bin/google-chrome')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-crash-reporter') 
    
    page = ChromiumPage(co)
    page.set.timeouts(page_load=15)
    
    loop_count, success_count = 0, 0
    current_ip = rotate_warp_ip("0.0.0.0")
    script_start_time = time.time() 
    
    while loop_count < MAX_LOOPS:
        if time.time() - script_start_time > 5.5 * 3600: break
        loop_count += 1
        try: page.get(URL)
        except: pass 
            
        countdown_ele = page.ele('#countdown', timeout=10)
        if not countdown_ele:
            current_ip = rotate_warp_ip(current_ip)
            continue
            
        current_time_text = countdown_ele.text
        if get_current_hours(current_time_text) >= TARGET_HOURS: break
            
        btn = page.ele('.vote-btn')
        if not btn or not btn.states.is_enabled:
            time.sleep(COOLDOWN_MINUTES * 60)
            current_ip = rotate_warp_ip(current_ip)
            continue
            
        try:
            btn.click(by_js=True)
            solve_turnstile(page)
            time.sleep(5)
            try: page.get(URL)
            except: pass
            new_time_text = page.ele('#countdown', timeout=10).text if page.ele('#countdown') else ""
            if current_time_text != new_time_text and new_time_text:
                success_count += 1
                if get_current_hours(new_time_text) >= TARGET_HOURS: break
                time.sleep(COOLDOWN_MINUTES * 60)
            current_ip = rotate_warp_ip(current_ip) 
        except: current_ip = rotate_warp_ip(current_ip)

    try: final_time, expiry_info = page.ele('#countdown').text, page.ele('.countdown-sub').text
    except: final_time, expiry_info = "未知", "未知"
    page.quit()
    
    send_tg_message(f"🎮 <b>G4F-US 续期战报</b>\n---\n🔄 循环消耗: {loop_count} 次\n✅ 成功暴击: {success_count} 次\n⏳ 存活时长: <code>{final_time}</code>\n📅 预计拔管: {expiry_info}")

if __name__ == '__main__': main()
