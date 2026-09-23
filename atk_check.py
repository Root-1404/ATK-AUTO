import requests
import os
import jwt
import time
import datetime
from playwright.sync_api import sync_playwright

# 从环境变量读取token，本地测试可直接赋值
token = os.getenv("ATK_TOKEN", "")
if not token:
    print("❌ 未读取到ATK_TOKEN，请检查环境变量配置")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Origin": "https://www.atkgear.com.cn",
    "Referer": "https://www.atkgear.com.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "client-type": "atk",
    "env": "prod"
}

def parse_jwt_remain_time(jwt_token: str):
    """解析JWT，计算剩余有效期，返回 天，小时"""
    try:
        payload = jwt.decode(jwt_token, options={"verify_signature": False})
        exp_ts = payload.get("exp")
        now_ts = int(time.time())
        remain_sec = exp_ts - now_ts
        if remain_sec <= 0:
            return 0, 0
        days = remain_sec // 86400
        hours = (remain_sec % 86400) // 3600
        return days, hours
    except Exception as e:
        print(f"⚠️ JWT解析异常: {str(e)}")
        return None, None

def get_checkin_stats():
    """获取签到统计"""
    url = "https://api.vxe.com/v1/member/checkin/stats"
    resp = requests.get(url, headers=headers, timeout=20)
    return resp.json()

def do_checkin():
    """执行签到"""
    url = "https://api.vxe.com/v1/member/checkin"
    resp = requests.post(url, headers=headers, timeout=20)
    return resp.json()

def clean_old_screenshots(save_dir="./screenshots", keep_count=1):
    """清理旧截图，只保留keep_count个最新文件"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        return
    file_list = []
    for fname in os.listdir(save_dir):
        if fname.lower().endswith(".png"):
            full_path = os.path.join(save_dir, fname)
            mtime = os.path.getmtime(full_path)
            file_list.append((mtime, full_path))
    # 按修改时间排序，旧的在前
    file_list.sort(key=lambda x: x[0])
    remove_num = len(file_list) - keep_count
    if remove_num > 0:
        for i in range(remove_num):
            _, path = file_list[i]
            os.remove(path)
            print(f"🧹 删除旧截图: {os.path.basename(path)}")

def take_status_screenshot(save_dir="./screenshots"):
    """打开ATK官网首页截图签到状态页面"""
    clean_old_screenshots(save_dir, keep_count=1)
    os.makedirs(save_dir, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_file = os.path.join(save_dir, f"atk_checkin_{now_str}.png")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        # 注入登录token到LocalStorage
        page = context.new_page()
        page.goto("https://www.atkgear.com.cn")
        # 写入LocalStorage登录凭证
        page.evaluate(f"""() => {{
            window.localStorage.setItem('token','{token}');
        }}""")
        page.reload()
        page.wait_for_timeout(3000)
        page.screenshot(path=save_file, full_page=True)
        browser.close()
    print(f"📸 状态截图已保存: {save_file}")
    return save_file

if __name__ == "__main__":
    # 打印JWT剩余有效期
    remain_days, remain_hours = parse_jwt_remain_time(token)
    if remain_days is not None:
        if remain_days <=0 and remain_hours <=0:
            print("⚠️ JWT Token已经过期！请立刻更新Token！")
        else:
            print(f"🔐 Token有效期剩余：{remain_days} 天 {remain_hours} 小时")

    stats = get_checkin_stats()
    print("\n📊 签到统计接口返回：")
    print(stats)
    data = stats.get("data", {})

    # 截图签到状态页面
    take_status_screenshot()

    if data.get("isCheckedInToday"):
        print("\nℹ️ 今日已经完成签到，无需重复执行")
    else:
        print("\n🚀 开始执行签到...")
        sign_result = do_checkin()
        print("✅ 签到接口返回结果：")
        print(sign_result)
