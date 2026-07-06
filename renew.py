import os, time, json, urllib.request, traceback
from seleniumbase import SB

TARGETS = [
    {"name": "nidaye", "url": "https://gaming4free.net/servers/nidaye"}
]

PROXY = "socks5://127.0.0.1:40000"

TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT = os.getenv("TG_CHAT_ID", "")


# --------------------------
# Telegram
# --------------------------
def tg(msg):
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": TG_CHAT, "text": msg}).encode()
        urllib.request.urlopen(
            urllib.request.Request(url, data, {'Content-Type': 'application/json'}),
            timeout=10
        )
    except:
        pass


# --------------------------
# 核心：抓 API vote（稳定判定）
# --------------------------
def extract_api_vote(sb):
    """
    直接从 Network 级别抓 API 返回（通过 page.evaluate hook）
    """

    try:
        data = sb.execute_script("""
            return window.__LAST_VOTE_RESPONSE || null;
        """)
        return data
    except:
        return None


# --------------------------
# 注入 XHR Hook（关键稳定点）
# --------------------------
def inject_api_hook(sb):
    sb.execute_script("""
        window.__LAST_VOTE_RESPONSE = null;

        const origFetch = window.fetch;

        window.fetch = async function(...args) {
            const res = await origFetch.apply(this, args);

            try {
                if (args[0] && args[0].includes('/vote')) {
                    const clone = res.clone();
                    clone.json().then(data => {
                        window.__LAST_VOTE_RESPONSE = data;
                    }).catch(()=>{});
                }
            } catch(e) {}

            return res;
        };
    """)


# --------------------------
# 主任务
# --------------------------
def run_task(target):
    name = target["name"]
    url = target["url"]

    try:
        with SB(uc=True, proxy=PROXY, headless=False, window_size="1920,1080") as sb:

            print(f"[{name}] 打开页面")
            sb.open(url)
            sb.sleep(8)

            # 注入 API hook（核心）
            inject_api_hook(sb)

            # 记录初始状态（API真值）
            sb.sleep(3)
            old_data = extract_api_vote(sb)

            old_hours = None
            if old_data and "hours_remaining" in old_data:
                old_hours = float(old_data["hours_remaining"])
                print(f"[{name}] 当前剩余时间: {old_hours}")

            # --------------------------
            # 点击 Vote（只触发，不做判断）
            # --------------------------
            print(f"[{name}] 点击 Vote")

            sb.execute_script("""
                let btns = document.querySelectorAll('button, a, div');
                for (let b of btns) {
                    let t = (b.innerText || '').toLowerCase();
                    if (t.includes('vote')) {
                        b.click();
                        break;
                    }
                }
            """)

            # --------------------------
            # 等待 API 回包
            # --------------------------
            print(f"[{name}] 等待 API 返回...")

            result = None
            for _ in range(30):
                result = extract_api_vote(sb)
                if result:
                    break
                time.sleep(1)

            # --------------------------
            # 判断核心（唯一真相）
            # --------------------------
            if not result:
                return "❌ 未获取到 API 返回"

            success = result.get("success", False)
            new_hours = result.get("hours_remaining", None)

            # --------------------------
            # 精准判断
            # --------------------------
            if success and new_hours is not None:

                if old_hours is not None:
                    if float(new_hours) > float(old_hours):
                        status = "✅ 续期成功"
                    else:
                        status = "⚠️ API成功但时间未变化"
                else:
                    status = "✅ API成功（无对比值）"

                msg = f"{status}\n{old_hours} → {new_hours}"

            else:
                msg = f"❌ 续期失败: {result}"

            # 截图
            os.makedirs("screenshots", exist_ok=True)
            sb.save_screenshot(f"screenshots/{name}.png")

            return msg

    except Exception as e:
        traceback.print_exc()
        return f"❌ 崩溃: {e}"


# --------------------------
# 主入口
# --------------------------
if __name__ == "__main__":
    print("\n===== V7 稳定 API 版启动 =====")

    results = []
    for t in TARGETS:
        res = run_task(t)
        results.append(res)

    report = "🤖 G4F 续期报告\n-------------------\n" + "\n".join(results)

    print(report)
    tg(report)
