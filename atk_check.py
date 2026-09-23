import requests
import os

# 从GitHub环境变量读取token
token = os.getenv("ATK_TOKEN")
if not token:
    print("❌ 未读取到ATK_TOKEN，请检查仓库Secret配置")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Origin": "https://www.atkgear.com.cn",
    "Referer": "https://www.atkgear.com.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def atk_checkin():
    url = "https://api.vxe.com/v1/user/checkin"
    try:
        resp = requests.post(url, headers=headers, timeout=15)
        res_data = resp.json()
        if resp.status_code == 200:
            if res_data.get("data", {}).get("success") is True:
                msg = res_data.get("data", {}).get("message", "")
                if "已记录" in msg:
                    print("✅ 签到成功！")
                else:
                    print(f"ℹ️ 接口返回：{msg}")
            else:
                print(f"⚠️ 签到失败：{res_data}")
        elif resp.status_code == 401:
            print("❌ Token已失效，请重新从浏览器复制新的Bearer Token！")
        else:
            print(f"❌ 请求异常，code:{resp.status_code}, 响应:{resp.text}")
    except Exception as e:
        print(f"❌ 网络异常：{str(e)}")

if __name__ == "__main__":
    atk_checkin()
