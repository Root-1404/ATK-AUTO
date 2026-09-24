import requests
import os
import jwt
import time
import datetime
from playwright.sync_api import sync_playwright

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
    url = "https://api.vxe.com/v1/member/checkin/stats"
    resp = requests.get(url, headers=headers, timeout=20)
    return resp.json()

def get_member_profile():
    url = "https://api.vxe.com/v1/member/profile"
    resp = requests.get(url, headers=headers, timeout=20)
    return resp.json()

def do_checkin():
    url = "https://api.vxe.com/v1/member/checkin"
    resp = requests.post(url, headers=headers, timeout=20)
    return resp.json()

def clean_old_screenshots(save_dir="./screenshots", keep_count=1):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        return
    file_list = []
    for fname in os.listdir(save_dir):
        if fname.lower().endswith(".png"):
            full_path = os.path.join(save_dir, fname)
            mtime = os.path.getmtime(full_path)
            file_list.append((mtime, full_path))
    file_list.sort(key=lambda x: x[0])
    remove_num = len(file_list) - keep_count
    if remove_num > 0:
        for i in range(remove_num):
            _, path = file_list[i]
            os.remove(path)
            print(f"🧹 删除旧截图: {os.path.basename(path)}")

def take_status_screenshot_by_html(stats_data, profile_data, remain_days, remain_hours, note_text="", save_dir="./screenshots"):
    clean_old_screenshots(save_dir, keep_count=1)
    os.makedirs(save_dir, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_file = os.path.join(save_dir, f"atk_checkin_{now_str}.png")
    html_path = os.path.join(save_dir, "temp.html")

    d = stats_data.get("data", {})
    p_data = profile_data.get("data", {})
    available_point = p_data.get("quantity", "获取失败")
    expire_point = p_data.get("aboutExpireQuantity", 0)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>ATK签到状态</title>
        <style>
            body {{font-family:system-ui;background:#1a1a1a;color:#fff;padding:30px;font-size:18px;}}
            .box {{border:1px solid #444;border-radius:12px;padding:24px;max-width:600px;margin:0 auto;}}
            .ok {{color:#4cd964;}}
            .no {{color:#ff3b30;}}
            .info {{color:#74b9ff;}}
            .warn {{color:#ff9500;}}
            .card {{border:1px solid #EEE;border-radius:8px;padding:16px;margin-bottom:20px;background:#222;}}
            .card-title {{font-size:16px;color:#aaa;margin-bottom:8px;}}
            .card-value {{font-size:32px;font-weight:bold;}}
            .note {{padding:8px;border-radius:6px;background:#333;margin:10px 0;color:#ffd166;}}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>ATK Gear 签到状态</h2>
            {f'<div class="note">执行备注：{note_text}</div>' if note_text else ''}
            <div class="card">
                <div class="card-title">可用积分</div>
                <div class="card-value">{available_point}</div>
            </div>
            <p>即将过期积分：{expire_point}</p>
            <p>今日已签到：<span class="{'ok' if d.get('isCheckedInToday') else 'no'}">{d.get('isCheckedInToday')}</span></p>
            <p>累计签到天数：{d.get('totalDays')}</p>
            <p>当前连续签到：{d.get('currentConsecutiveDays')}</p>
            <p>最大连续签到：{d.get('maxConsecutiveDays')}</p>
            <p>总积分：{d.get('totalPoints')}</p>
            <p>上次签到日期：{d.get('lastCheckinDate')}</p>
            <p>下次奖励：{d.get('nextRewardDays')}天后，+{d.get('nextRewardPoints')}积分</p>
            <p class="info">Token有效期剩余：{remain_days} 天 {remain_hours} 小时</p>
            <p>截图时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{os.path.abspath(html_path)}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=save_file, full_page=True)
        browser.close()
    os.remove(html_path)
    print(f"📸 签到状态截图已保存: {save_file}")
    return save_file

if __name__ == "__main__":
    remain_days, remain_hours = parse_jwt_remain_time(token)
    if remain_days is not None:
        if remain_days <=0 and remain_hours <=0:
            print("⚠️ JWT Token已经过期！请立刻更新Token！")
        else:
            print(f"🔐 Token有效期剩余：{remain_days} 天 {remain_hours} 小时")
            if remain_days < 3:
                print("❗ 警告：Token剩余不足3天，请尽快更换！")

    # ===== 获取签到前状态 =====
    stats_before = get_checkin_stats()
    profile_before = get_member_profile()
    print("\n📊【签到前】签到统计接口返回：")
    print(stats_before)
    print("\n👤【签到前】用户资料接口返回：")
    print(profile_before)

    data_before = stats_before.get("data", {})

    if data_before.get("isCheckedInToday"):
        print("\nℹ️ 今日已经完成签到，无需重复执行")
        take_status_screenshot_by_html(stats_before, profile_before, remain_days, remain_hours, note_text="无需签到，今日已签")
    else:
        print("\n🚀 开始执行签到...")
        sign_result = do_checkin()
        print("✅ 签到接口返回结果：")
        print(sign_result)
        # ===== 签到完成，重新拉取最新状态 =====
        time.sleep(2)
        stats_after = get_checkin_stats()
        profile_after = get_member_profile()
        print("\n📊【签到后】签到统计接口返回：")
        print(stats_after)
        print("\n👤【签到后】用户资料接口返回：")
        print(profile_after)

        # 校验签到结果
        data_after = stats_after.get("data", {})
        if data_after.get("isCheckedInToday") is True:
            print("\n✅ 校验通过：签到成功，isCheckedInToday已更新为true")
            note = "已执行一次签到请求，校验签到成功"
        else:
            print("\n⚠️⚠️⚠️ 校验告警：已经调用签到接口，但isCheckedInToday仍然为false！可能受UTC时区限制/接口异常！")
            note = "⚠️校验告警：调用签到后状态未变更，注意UTC时区问题"

        take_status_screenshot_by_html(stats_after, profile_after, remain_days, remain_hours, note_text=note)
