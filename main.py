import requests
import time
import os

# ------------------ 配置区 ------------------ #

# 从 Replit Secrets (环境变量) 读取 URL 列表
# 格式应该是：https://url1.com,https://url2.com,https://url3.net
urls_str = os.getenv('URLS_TO_MONITOR')

if not urls_str:
    print("错误：请在 Replit 的 Secrets 中设置 'URLS_TO_MONITOR'")
    # 你也可以在这里设置一个默认列表用于测试，但不推荐用于生产
    # urls_str = "https://your-first-repl.replit.dev/,https://your-second-repl.replit.dev/"
    exit()

URLS = [url.strip() for url in urls_str.split(',')]

# 每隔多少秒 ping 一次 (推荐 60-240 秒之间)
PING_INTERVAL = 30  # 单位：秒

# ------------------------------------------- #

def ping_urls():
    """循环遍历 URL 列表并发送 GET 请求"""
    for url in URLS:
        try:
            # 设置超时以防某个项目响应过慢
            response = requests.get(url, timeout=10)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Pinging {url} ... Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Pinging {url} ... Error: {e}")

if __name__ == "__main__":
    print("🚀 Replit Keep-Alive Watcher 已启动！")
    print(f"🕒 监控间隔: {PING_INTERVAL} 秒")
    print("🎯 监控目标:")
    for i, url in enumerate(URLS):
        print(f"  {i+1}. {url}")
    print("-" * 30)

    while True:
        ping_urls()
        time.sleep(PING_INTERVAL)
