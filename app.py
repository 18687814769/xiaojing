import streamlit as st
import requests
import xml.etree.ElementTree as ET
import time
import json
import pandas as pd
import os
from datetime import datetime

# ================= 配置区域 =================
try:
    API_KEY = st.secrets["nvidia"]["api_key"]
    if not API_KEY or not API_KEY.startswith("nvapi-"):
        st.error("⚠️ API Key 格式不正确！")
        st.stop()
except KeyError:
    st.error("⚠️ 未找到 API Key，请检查 Secrets。")
    st.stop()

BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_STRONG = "meta/llama-3.1-405b-instruct"
MODEL_FAST = "meta/llama-3.1-70b-instruct"

# 数据日志文件
LOG_FILE = "usage_log.csv"

# ==========================================

# --- 初始化页面状态 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_phone' not in st.session_state:
    st.session_state.user_phone = ""
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False

# --- 数据记录函数 ---
def log_usage(feature, prompt, result):
    """记录使用数据到 CSV"""
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.user_phone,
        "feature": feature,
        "prompt": prompt[:50] + "...", # 只记前50字
        "status": "success" if "❌" not in str(result) else "failed"
    }
    df = pd.DataFrame([data])
    if not os.path.exists(LOG_FILE):
        df.to_csv(LOG_FILE, index=False)
    else:
        df.to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- 核心函数：Google News RSS ---
def search_google_news(query, num_results=3):
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:2d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = []
            for item in root.findall('.//item'):
                title = item.find('title').text
                link = item.find('link').text
                if link.startswith('/'):
                    link = "https://news.google.com" + link
                items.append(f"- **{title.split('-')[0]}**")
                if len(items) >= num_results:
                    break
            return "\n".join(items) if items else "暂无新闻。"
        else:
            return "搜索服务暂时不可用。"
    except Exception as e:
        return "搜索失败。"

# --- 核心函数：调用 NVIDIA AI (带小景建议) ---
def call_nvidia(prompt, model, system_prompt="你是一个有用的助手。", search_context=None, add_insight=False):
    if search_context and search_context != "未找到最新相关新闻。":
        final_prompt = f"请根据以下最新资讯回答问题：{search_context}\n\n问题：{prompt}"
    else:
        final_prompt = prompt
    
    if add_insight:
        final_prompt += "\n\n【重要】请在回答最后，单独起一段，以 '💡 小景建议：' 开头，给出一条具体的行动建议、风险提示或优化方案。"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ 错误：{response.status_code}"
    except Exception as e:
        return f"❌ 请求失败"

# --- 登录页面 ---
def login_page():
    st.title("📱 小景 AI")
    st.markdown("让 AI 成为你的超级员工")
    st.divider()
    
    st.markdown("### 🔒 安全登录")
    phone = st.text_input("请输入手机号", placeholder="138****8888")
    code = st.text_input("请输入验证码", placeholder="输入 1234")
    
    if st.button("登录/注册", use_container_width=True):
        if code == "1234" and len(phone) > 0:
            st.session_state.logged_in = True
            st.session_state.user_phone = phone
            st.rerun()
        else:
            st.warning("验证码错误 (试试 1234) 或手机号未填")

# --- 主界面 ---
def main_page():
    # 侧边栏
    with st.sidebar:
        st.title("小景智能体")
        st.markdown(f"👤 用户：{st.session_state.user_phone}")
        st.divider()
        menu = st.radio("选择功能", ["📊 智能研报", "📝 会议纪要", "🎨 爆款文案", "🎨 AI 绘画"], index=0)
        st.divider()
        if st.button("🔒 管理员入口"):
            st.session_state.show_admin = True
            st.rerun()
        if st.button("退出登录"):
            st.session_state.logged_in = False
            st.rerun()

    # 管理员入口
    if st.session_state.get('show_admin', False):
        admin_page()
        return

    # 功能逻辑
    if menu == "📊 智能研报":
        st.header("📊 智能研报")
        st.info("💡 基于 **Llama 3.1 405B** + 实时新闻 + 小景建议")
        topic = st.text_input("行业或主题")
        if st.button("🚀 生成研报"):
            if not topic:
                st.warning("请输入主题")
            else:
                with st.spinner('🔍 搜索新闻中...'):
                    news = search_google_news(topic)
                with st.spinner('🤖 分析中...'):
                    prompt = f"为'{topic}'写一份简短研报。1.核心动态 2.关键数据 3.建议。"
                    report = call_nvidia(prompt, MODEL_STRONG, search_context=news, add_insight=True)
                    if "❌" in report:
                        st.error(report)
                    else:
                        st.success("✅ 完成")
                        st.markdown(report)
                        log_usage("研报", topic, report)

    elif menu == "📝 会议纪要":
        st.header("📝 会议纪要")
        raw_text = st.text_area("粘贴会议记录", height=150)
        if st.button("🪄 一键整理"):
            if not raw_text:
                st.warning("请输入内容")
            else:
                with st.spinner('🤖 整理中...'):
                    prompt = f"整理会议记录：1.核心决策 2.待办 3.风险。内容：{raw_text}"
                    summary = call_nvidia(prompt, MODEL_FAST, add_insight=True)
                    if "❌" in summary:
                        st.error(summary)
                    else:
                        st.success("✅ 完成")
                        st.markdown(summary)
                        log_usage("纪要", raw_text[:50], summary)

    elif menu == "🎨 爆款文案":
        st.header("🎨 爆款文案")
        theme = st.text_input("产品或主题")
        if st.button("✍️ 创作"):
            if not theme:
                st.warning("请输入主题")
            else:
                with st.spinner('🤖 创作中...'):
                    prompt = f"为'{theme}'写 3 个爆款文案（震惊体、专业体、亲切体）。"
                    result = call_nvidia(prompt, MODEL_FAST, add_insight=True)
                    if "❌" in result:
                        st.error(result)
                    else:
                        st.success("✅ 完成")
                        st.markdown(result)
                        log_usage("文案", theme, result)

    elif menu == "🎨 AI 绘画":
        st.header("🎨 AI 绘画")
        st.info("基于 **Stable Diffusion XL** (功能开发中，敬请期待...)")
        st.markdown("*(此功能需额外配置 NVIDIA 文生图接口，当前版本暂不可用)*")

# --- 管理员页面 ---
def admin_page():
    st.header("📊 数据驾驶舱")
    st.markdown(f"当前管理员：**{st.session_state.user_phone}**")
    
    if st.button("返回主页"):
        st.session_state.show_admin = False
        st.rerun()
    
    st.divider()
    
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总调用次数", len(df))
        with col2:
            today = datetime.now().strftime("%Y-%m-%d")
            st.metric("今日调用", len(df[df['timestamp'].str.contains(today)]))
        
        st.write("### 最近记录")
        st.dataframe(df.tail(10).sort_values(by="timestamp", ascending=False)) # 显示最近 10 条
    else:
        st.info("暂无数据")

# --- 主逻辑 ---
if not st.session_state.logged_in:
    login_page()
else:
    main_page()
