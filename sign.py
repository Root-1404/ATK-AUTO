import os
import time
import random
from playwright.sync_api import sync_playwright, Page

# ====================== 配置区 ======================
MAX_RETRY = 3  # 最大重试次数
RANDOM_WAIT_MIN = 60   # 脚本启动后，随机等待最小秒数
RANDOM_WAIT_MAX = 180  # 脚本启动后，随机等待最大秒数
SAVE_SCREENSHOT_PATH = "error_screenshot.png"

# XPATH
ENTRY_XPATH = '//*[@id="__nuxt"]/div/div/div[1]/div[2]/div/div[1]/div[2]/div[4]/div[3]'
SIGN_BTN_XPATH = '//*[@id="__nuxt"]/div/div/div[1]/div[2]/div/div[3]/div[2]/div/div/div[3]'
# ====================================================

def add_cookies(page: Page, cookie_str: str):
    """把字符串cookie转为playwright cookie字典数组"""
    cookies = []
    for item in cookie_str.split(";"):
        item = item.strip()
        if not item:
            continue
        k, v = item.split("=", 1)
        cookies.append({
            "name": k,
            "value": v,
            "domain": ".atkgear.com.cn/pointmall/mallcenter", # !!!【重要】替换成目标网站域名，例如 .xxx.com
            "path": "/",
        })
    page.context.add_cookies(cookies)

def run_sign():
    cookie_str = os.getenv("user_cookie")
    if not cookie_str:
        print("❌ 环境变量 user_cookie 为空，请检查仓库Secrets")
        return False

    print(f"⏳ 随机等待 {RANDOM_WAIT_MIN} ~ {RANDOM_WAIT_MAX} 秒再开始签到")
    random_sleep = random.randint(RANDOM_WAIT_MIN, RANDOM_WAIT_MAX)
    time.sleep(random_sleep)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width":1280, "height":720})
        page = context.new_page()

        # 设置cookie
        add_cookies(page, cookie_str)
        # !!!【重要】替换为目标网站主页URL
        page.goto("https://www.atkgear.com.cn/pointmall/mallcenter")

        try:
            # 1. 进入签到入口
            print("🔍 寻找签到入口")
            entry = page.wait_for_selector(f"xpath={ENTRY_XPATH}", timeout=15000)
            entry.click()
            time.sleep(2)

            # 2. 寻找签到按钮并点击
            print("🔍 寻找签到按钮，准备点击")
            sign_btn = page.wait_for_selector(f"xpath={SIGN_BTN_XPATH}", timeout=15000)
            sign_btn.click()
            time.sleep(3)

            # ==========【你需要自行修改】签到成功判断逻辑 ==========
            # 方案1：识别页面上“签到成功”文字，自行修改文字内容
            success_text = page.locator("text=签到日历").wait_for(timeout=5000)
            if success_text:
                print("✅ 签到执行成功！")
                browser.close()
                return True
        except Exception as e:
            print(f"⚠️ 本次签到失败: {e}")
            # 失败截图
            page.screenshot(path=SAVE_SCREENSHOT_PATH)
            print(f"📸 错误截图已保存至 {SAVE_SCREENSHOT_PATH}")
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
        print(f"等待10秒后重试...")
        time.sleep(10)

    if not success:
        print(f"❌ 已重试{MAX_RETRY}次，签到全部失败！")
        exit(1)  # 返回非0，让Action标记任务失败

if __name__ == "__main__":
    main()
