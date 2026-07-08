#!/usr/bin/env python3
"""
Gaming4Free 自动续期 — GitHub Actions 版本
每次运行投 1 票，配合每小时 cron 保持服务器在线。
"""
import os, sys, time, urllib.request, json, re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGETS = [{"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}]
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")


def send_tg(msg: str):
    if not TG_TOKEN or not TG_CHAT:
        print("⚠️ 未配置 TG_TOKEN/TG_CHAT_ID，跳过通知")
        return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        print("✅ Telegram 通知已发送")
    except Exception as e:
        print(f"❌ Telegram 通知失败: {e}")


def make_driver():
    opts = Options()
    opts.headless = True
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-setuid-sandbox")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=opts)


def vote_once(name, url):
    """执行一次投票，返回 (status, timer_text)"""
    driver = None
    try:
        driver = make_driver()
        wait = WebDriverWait(driver, 20)
        print(f"  📄 打开 {url}")
        driver.get(url)

        # 获取当前计时器
        timer_text = "未知"
        try:
            timer_el = wait.until(EC.presence_of_element_located((By.ID, "sd-timer")))
            timer_text = timer_el.get_attribute("textContent").strip()
            print(f"  ⏱️  当前计时器: {timer_text}")
        except Exception:
            print("  ⚠️  未获取到计时器")

        # 检查是否已过期
        if timer_text.upper() == "EXPIRED":
            return ("⚠️  服务器已过期", timer_text)

        # 点击投票按钮
        vote_btn = wait.until(EC.presence_of_element_located((By.ID, "sd-vote-btn")))
        print("  🖱️  点击投票按钮...")
        vote_btn.click()
        time.sleep(4)

        # 等待 Turnstile 通过 + 弹窗渲染
        print("  ⏳ 等待 Turnstile 验证和弹窗加载...")
        time.sleep(6)

        # 提交投票
        print("  🖱️  点击提交按钮 #vm-submit...")
        try:
            submit = wait.until(EC.element_to_be_clickable((By.ID, "vm-submit")))
            submit.click()
        except Exception:
            print("  ⚠️  点击提交失败，尝试 JS...")
            driver.execute_script("document.getElementById('vm-submit').click();")

        # 等待投票处理
        print("  ⏳ 等待投票处理...")
        time.sleep(15)

        # 刷新页面检查结果
        driver.get(url)
        time.sleep(5)

        try:
            timer_el = wait.until(EC.presence_of_element_located((By.ID, "sd-timer")))
            new_timer = timer_el.get_attribute("textContent").strip()
            print(f"  ⏱️  新计时器: {new_timer}")
            timer_text = new_timer
        except Exception:
            print("  ⚠️  获取新计时器失败")

        # 判断是否成功
        if re.search(r"\d", timer_text) and timer_text.upper() != "EXPIRED":
            return ("✅ 投票成功", timer_text)
        else:
            return ("❌ 投票失败", timer_text)

    except Exception as e:
        return (f"❌ 异常: {e}", "未知")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def main():
    print("=" * 50)
    print("🤖 Gaming4Free 自动续期")
    print("=" * 50)

    results = []

    for target in TARGETS:
        name = target["name"]
        url = target["url"]
        print(f"\n🎮 节点: {name} | {url}")

        status, timer = vote_once(name, url)
        print(f"\n  ✅ 结果: {status} | 计时器: {timer}")

        results.append({"name": name, "status": status, "timer": timer})

    # 汇总通知
    print(f"\n{'='*50}")
    print("📊 执行汇总")
    print("=" * 50)
    for r in results:
        print(f"  {r['name']}: {r['status']} | {r['timer']}")

    if results:
        last = results[-1]
        msg = f"🤖 Gaming4Free 续期结果\n\n节点: {last['name']}\n状态: {last['status']}\n剩余时间: {last['timer']}"
        send_tg(msg)


if __name__ == "__main__":
    main()
