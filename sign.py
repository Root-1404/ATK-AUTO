import os
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
import os
# 启动前删除旧截图
if os.path.exists("error_screenshot.png"):
    os.remove("error_screenshot.png")
# ====================== 配置区 ======================
MAX_RETRY = 3  # 最大重试次数
RANDOM_WAIT_MIN = 60   # 脚本启动后随机等待最小秒
RANDOM_WAIT_MAX = 180  # 脚本启动后随机等待最大秒
SAVE_SCREENSHOT_PATH = "error_screenshot.png"
SITE_DOMAIN = ".atkgear.com.cn"
SITE_URL = "https://www.atkgear.com.cn/pointmall/mallcenter"
# ====================================================

def add_cookies(page: Page, cookie_str: str, domain: str):
    cookies = []
    for item in cookie_str.split(";"):
        item = item.strip()
        if not item:
            continue
        k, v = item.split("=", 1)
        cookies.append({
            "name": k,
            "value": v,
            "domain": domain,
            "path": "/",
        })
    page.context.add_cookies(cookies)

def run_sign():
    cookie_str = os.getenv("user_cookie")
    if not cookie_str:
        print("❌ 环境变量 user_cookie 为空，请检查仓库Secrets")
        return False

    print(f"⏳ 随机等待 {RANDOM_WAIT_MIN} ~ {RANDOM_WAIT_MAX} 秒后开始签到")
    random_sleep = random.randint(RANDOM_WAIT_MIN, RANDOM_WAIT_MAX)
    time.sleep(random_sleep)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width":1280, "height":720})
        page = context.new_page()

        # 设置Cookie
        add_cookies(page, cookie_str, SITE_DOMAIN)
        print(f"🌐 访问页面 {SITE_URL}")
        page.goto(SITE_URL, timeout=30000)
        time.sleep(3)

        try:
            # 判断今日是否已经签到
            already_sign_elem = page.locator("text=今日已签到")
            if already_sign_elem.is_visible(timeout=5000):
                print("✅ 检测到【今日已签到】，无需重复签到！")
                browser.close()
                return True
        except Exception:
            print("ℹ️ 未检测到今日已签到，准备执行签到")

        try:
            # 定位【立即签到】按钮并点击
            sign_btn = page.locator("text=签到日历")
            sign_btn.wait_for(state="visible", timeout=15000)
            sign_btn.click()
            print("🖱️ 点击签到按钮成功，等待页面刷新")
            time.sleep(4)

            # 点击后校验：是否变成今日已签到
            if page.locator("text=今日已签到").is_visible(timeout=8000):
                print("✅ 签到完成，页面显示今日已签到！")
                browser.close()
                return True
            else:
                raise Exception("点击签到按钮后，页面没有变成今日已签到，签到失败")

        except Exception as e:
            print(f"⚠️ 本次签到异常: {e}")
            # 失败时全屏截图
            page.screenshot(path=SAVE_SCREENSHOT_PATH, full_page=True)
            print(f"📸 错误截图已保存: {SAVE_SCREENSHOT_PATH}")
            browser.close()
            return False

def main():
    retry_count = 0
    success = False
    while retry_count < MAX_RETRY:
        retry_count += 1
        print(f"\n===== 第 {retry_count}/{MAX_RETRY} 次尝试签到 =====")
        success = run_sign()
        if success:
            break
        print(f"⏱️ 等待10秒后进行下一次重试...")
        time.sleep(10)

    if not success:
        print(f"❌ 已重试{MAX_RETRY}次，签到全部失败！")
        exit(1) # 非0退出，标记Action任务失败

if __name__ == "__main__":
    main()
