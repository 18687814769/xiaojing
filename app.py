import streamlit as st
import requests
import xml.etree.ElementTree as ET
import time

# ================= 配置区域 =================
try:
    API_KEY = st.secrets["nvidia"]["api_key"]
    if not API_KEY or not API_KEY.startswith("nvapi-"):
        st.error("⚠️ 严重错误：API Key 格式不正确！")
        st.stop()
except KeyError:
    st.error("⚠️ 严重错误：未在 Secrets 中找到 NVIDIA API Key。")
    st.stop()
except Exception as e:
    st.error(f"⚠️ 读取配置出错：{str(e)}")
    st.stop()

BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# 【修正】全部使用 NVIDIA 上真实存在的模型！
# 1. 最强逻辑：Llama 3.1 405B (适合研报)
MODEL_STRONG = "meta/llama-3.1-405b-instruct"
# 2. 快速响应：Llama 3.1 70B (适合纪要、文案，速度快，中文也不错)
MODEL_FAST = "meta/llama-3.1-70b-instruct"

# ==========================================
st.set_page_config(page_title="小景智能体 | 真实模型版", layout="wide")

# --- 自定义 CSS ---
st.markdown("""
<style>
.stApp { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
h1 { color: #4f46e5; font-weight: 800; text-align: center; }
.stButton>button { background-color: #76b900; color: white; border-radius: 6px; font-weight: 600; border: none; width: 100%; font-size: 1.1rem; }
.stButton>button:hover { background-color: #5a8f00; }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏 ---
with st.sidebar:
    st.title("小景智能体")
    st.markdown("**让 AI 成为你的超级员工**")
    st.divider()
    menu = st.radio("选择功能", ["📊 智能研报 (Google News)", "📝 会议纪要", "🎨 爆款文案 (Google News)"])
    st.divider()
    st.markdown("© 2026 小景智能体科技")

# --- 核心函数：Google News RSS ---
def search_google_news(query, num_results=5):
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:2d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = []
            for item in root.findall('.//item'):
                title = item.find('title').text
                link = item.find('link').text
                if link.startswith('/'): link = "https://news.google.com" + link
                pub_date = item.find('pubDate').text
                items.append(f"- **{title}** ({pub_date}) [来源]({link})")
                if len(items) >= num_results: break
            if items: return "以下是 Google News 最新实时资讯：\n\n" + "\n".join(items)
            else: return "未找到最新相关新闻。"
        else: return f"搜索服务暂时不可用 (状态码：{response.status_code})。"
    except Exception as e: return f"搜索失败：{str(e)}"

# --- 核心函数：调用 NVIDIA AI ---
def call_nvidia(prompt, model, system_prompt="你是一个有用的助手。", search_context=None):
    if search_context and search_context != "未找到最新相关新闻。":
        final_prompt = f"请根据以下【最新实时资讯】回答问题。\n\n【最新资讯】:\n{search_context}\n\n【用户问题】:\n{prompt}"
    else:
        final_prompt = prompt

    headers = { "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json" }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        elif response.status_code == 404:
            return f"❌ 请求的资源不存在 (404)。\n模型名称 '{model}' 可能错误。\n原始信息：{response.text}"
        elif response.status_code == 401:
            return f"❌ 认证失败 (401)：API Key 无效。\n原始信息：{response.text}"
        elif response.status_code == 429:
            return f"⚠️ 请求过快 (429)。\n原始信息：{response.text}"
        elif response.status_code == 503:
            return f"⚠️ 服务不可用 (503)。\n原始信息：{response.text}"
        else:
            return f"❌ 服务繁忙 ({response.status_code})。\n原始信息：{response.text}"
    except Exception as e:
        return f"❌ 网络请求失败：{str(e)}"

# --- 主界面 ---
st.title("🌐 小景智能体 (真实模型版)")
st.markdown('<p class="subtitle">使用 NVIDIA 真实存在的 Llama 3.1 系列模型</p>', unsafe_allow_html=True)

if menu == "📊 智能研报 (Google News)":
    st.header("📊 智能研报生成器")
    st.info("💡 使用 **Llama 3.1 405B** (最强模型) 生成深度研报。")
    topic = st.text_input("请输入行业或主题")
    if st.button("🚀 开始生成研报"):
        if not topic: st.warning("请输入主题！")
        else:
            with st.spinner(f'🔍 正在抓取 "{topic}" 的最新 Google News...'):
                news = search_google_news(topic)
                if "搜索失败" in news or "不可用" in news:
                    st.warning(f"⚠️ {news} 将尝试使用模型内部知识。")
                    news = None
            with st.spinner('🤖 正在生成研报...'):
                prompt = f"请作为资深分析师，为'{topic}'写一份研报。要求：1.核心动态 2.关键数据 3.小景建议。"
                report = call_nvidia(prompt, MODEL_STRONG, "你是一位顶级行业分析师。", search_context=news)
                if "❌" in report or "⚠️" in report: st.error(report)
                else:
                    st.success("✅ 分析完成！")
                    st.markdown(report)
                    st.download_button("📥 下载报告", report, file_name=f"{topic}_report.md")

elif menu == "📝 会议纪要":
    st.header("📝 会议纪要整理助手")
    st.info("💡 使用 **Llama 3.1 70B** (快速模型) 整理纪要。")
    raw_text = st.text_area("请粘贴会议记录", height=200)
    if st.button("🪄 一键整理"):
        if not raw_text: st.warning("请输入内容！")
        else:
            with st.spinner('🤖 正在整理...'):
                prompt = f"请整理会议记录：1.核心决策 2.待办事项 3.潜在风险。内容：{raw_text}"
                summary = call_nvidia(prompt, MODEL_FAST, "你是一位高效的会议秘书。")
                if "❌" in summary or "⚠️" in summary: st.error(summary)
                else:
                    st.success("✅ 整理完成！")
                    st.markdown(summary)

elif menu == "🎨 爆款文案 (Google News)":
    st.header("🎨 爆款文案生成器")
    st.info("💡 使用 **Llama 3.1 70B** (快速模型) 生成文案。")
    theme = st.text_input("请输入产品或主题")
    if st.button("✍️ 开始创作"):
        if not theme: st.warning("请输入主题！")
        else:
            with st.spinner(f'🔍 正在抓取 "{theme}" 的最新热点...'):
                news = search_google_news(theme)
                if "搜索失败" in news or "不可用" in news:
                    st.warning(f"⚠️ {news} 将尝试使用模型内部知识。")
                    news = None
            with st.spinner('🤖 正在创作...'):
                prompt = f"请为'{theme}'写 3 个爆款文案（震惊体、专业体、亲切体）。"
                result = call_nvidia(prompt, MODEL_FAST, "你是一位新媒体专家。", search_context=news)
                if "❌" in result or "⚠️" in result: st.error(result)
                else:
                    st.success("✅ 创作完成！")
                    st.markdown(result)
