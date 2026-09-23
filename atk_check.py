import requests
import os

# token从环境变量读取，本地测试直接赋值
token = os.getenv("ATK_TOKEN", "在此处填入你的JWT，不要加Bearer前缀")

headers = {
    "Authorization": f"Bearer {token}",
    "Origin": "https://www.atkgear.com.cn",
    "Referer": "https://www.atkgear.com.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "client-type": "atk",
    "env": "prod"
}

def get_checkin_stats():
    """获取签到统计：判断今日是否已经签到"""
    url = "https://api.vxe.com/v1/member/checkin/stats"
    resp = requests.get(url, headers=headers, timeout=20)
    return resp.json()

def do_checkin():
    """执行签到 POST /v1/member/checkin"""
    url = "https://api.vxe.com/v1/member/checkin"
    resp = requests.post(url, headers=headers, timeout=20)
    return resp.json()

if __name__ == "__main__":
    stats = get_checkin_stats()
    print("📊 签到统计接口返回：")
    print(stats)
    data = stats.get("data", {})
    if data.get("isCheckedInToday"):
        print("\nℹ️ 今日已经完成签到，无需重复执行")
    else:
        print("\n🚀 开始执行签到...")
        sign_result = do_checkin()
        print("✅ 签到接口返回结果：")
        print(sign_result)
