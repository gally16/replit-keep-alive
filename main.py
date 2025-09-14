import os
import time
import requests
import threading
from flask import Flask, render_template_string

# ------------------ 配置区 ------------------ #
# 从 Replit Secrets 读取 URL 列表
urls_str = os.getenv('URLS_TO_MONITOR')
if not urls_str:
    # 如果 Secrets 中没有设置，使用一个示例 URL 方便测试
    print("警告：未在 Secrets 中找到 'URLS_TO_MONITOR'。正在使用示例 URL。")
    urls_str = "https://www.google.com" # 这是一个示例

URLS = [url.strip() for url in urls_str.split(',') if url.strip()]
PING_INTERVAL = 60  # 单位：秒

# ------------------ 全局状态存储 ------------------ #
# 这个字典将由后台线程更新，并由 Flask 前台读取
# 格式: {"url": {"status": "...", "timestamp": "..."}}
monitoring_status = {url: {"status": "Pending...", "timestamp": "-"} for url in URLS}
status_lock = threading.Lock() # 使用锁来确保线程安全

# ------------------ HTML 模板 ------------------ #
# 我们将 HTML 直接写在代码里，方便管理
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60"> <!-- 每 60 秒自动刷新页面 -->
    <title>Replit Keep-Alive Status</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f0f2f5; color: #333; margin: 0; padding: 2em; }
        .container { max-width: 800px; margin: 0 auto; background-color: #fff; padding: 2em; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1 { color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 0.5em; }
        .status-list { list-style: none; padding: 0; }
        .status-item { display: flex; justify-content: space-between; align-items: center; padding: 1em; border-bottom: 1px solid #eee; transition: background-color 0.3s; }
        .status-item:last-child { border-bottom: none; }
        .status-item:hover { background-color: #f9f9f9; }
        .url { word-break: break-all; margin-right: 1em; }
        .status { font-weight: bold; padding: 0.3em 0.8em; border-radius: 12px; font-size: 0.9em; white-space: nowrap; }
        .status-ok { color: #28a745; background-color: #e9f5ec; }
        .status-error { color: #dc3545; background-color: #fbebed; }
        .status-pending { color: #6c757d; background-color: #f0f2f5; }
        .timestamp { font-size: 0.8em; color: #6c757d; text-align: right; }
        footer { margin-top: 2em; text-align: center; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Replit Watcher Status</h1>
        <ul class="status-list">
            {% for url, data in statuses.items() %}
                <li class="status-item">
                    <div>
                        <div class="url"><a href="{{ url }}" target="_blank">{{ url }}</a></div>
                        <div class="timestamp">Last check: {{ data.timestamp }}</div>
                    </div>
                    {% if 'Error' in data.status or '503' in data.status %}
                        <span class="status status-error">{{ data.status }}</span>
                    {% elif '200' in data.status %}
                        <span class="status status-ok">{{ data.status }}</span>
                    {% else %}
                        <span class="status status-pending">{{ data.status }}</span>
                    {% endif %}
                </li>
            {% endfor %}
        </ul>
    </div>
    <footer>Page automatically refreshes every 60 seconds.</footer>
</body>
</html>
"""

# ------------------ 后台 Pinger 线程 ------------------ #
def pinger_thread_func():
    """这个函数在后台无限循环，ping 所有 URL 并更新全局状态字典"""
    while True:
        for url in URLS:
            status_text = ""
            try:
                response = requests.get(url, timeout=15)
                status_text = f"Status: {response.status_code}"
            except requests.exceptions.RequestException as e:
                # 简化错误信息
                status_text = f"Error: {type(e).__name__}"
            
            # 使用锁安全地更新状态
            with status_lock:
                monitoring_status[url] = {
                    "status": status_text,
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC')
                }
            
            # 在 ping 每个 URL 之间稍微停顿一下，避免瞬间产生大量请求
            time.sleep(1) 

        time.sleep(PING_INTERVAL)

# ------------------ Flask Web 服务器 ------------------ #
app = Flask(__name__)

@app.route('/')
def status_dashboard():
    """这是 Web 页面的主路由，它会读取全局状态并渲染 HTML"""
    with status_lock:
        # 创建状态字典的副本以进行渲染
        current_statuses = monitoring_status.copy()
    return render_template_string(HTML_TEMPLATE, statuses=current_statuses)

# ------------------ 主程序入口 ------------------ #
if __name__ == "__main__":
    print("🚀 Replit Keep-Alive Watcher (Web UI) 正在启动...")
    
    # 1. 启动后台 pinger 线程
    # 设置为 daemon=True 意味着当主程序退出时，这个线程也会自动退出
    pinger = threading.Thread(target=pinger_thread_func, daemon=True)
    pinger.start()
    print("✅ 后台监控线程已启动。")
    
    # 2. 启动 Flask Web 服务器
    # Replit 需要 host='0.0.0.0' 才能对外提供服务
    print(f"🌍 Web UI 将在 http://0.0.0.0:8080 上运行。")
    app.run(host='0.0.0.0', port=8080)
