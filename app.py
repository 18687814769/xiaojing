import streamlit as st
import requests
import xml.etree.ElementTree as ET
import time

# ================= 配置区域 =================
try:
    API_KEY = st.secrets["nvidia"]["api_key"]
except KeyError:
    st.error("⚠️ 严重错误：未在 secrets.toml 中找到 NVIDIA 密钥！")
    st.stop()

BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_LLAMA = "meta/llama-3.1-405b-instruct"
MODEL_QWEN = "qwen/qwen2.5-72b-instruct"
# ==========================================

st.set_page_config(page_title="小景智能体 | Google News 版", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
h1 { color: #4f46e5; font-weight: 800; text-align: center; }
.stButton>button { background-color: #76b900; color: white; border-radius: 6px; font-weight: 600; border: none; width: 100%; font-size: 1.1rem; }
.stButton>button:hover { background-color: #5a8f00; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("小景智能体")
    st.markdown("**让 AI 成为你的超级员工**")
    st.divider()
    menu = st.radio("选择功能", ["📊 智能研报 (Google News)", "📝 会议纪要", "🎨 爆款文案 (Google News)"])
    st.divider()
    st.markdown("© 2026 小景智能体科技")

# --- 核心函数：Google News RSS 搜索 (无需安装库) ---
def search_google_news(query, num_results=5):
    """抓取 Google News RSS 源"""
    # 构造 RSS  URL
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+when:2d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = []
            # 解析 XML
            for item in root.findall('.//item'):
                title = item.find('title').text
                link = item.find('link').text
                # 有些链接是相对的，需要补全
                if link.startswith('/'): link = "https://news.google.com" + link
                pub_date = item.find('pubDate').text
                items.append(f"- **{title}** ({pub_date}) [来源]({link})")
                if len(items) >= num_results:
                    break
            if items:
                return "以下是 Google News 最新实时资讯：\n\n" + "\n".join(items)
            else:
                return "未找到最新相关新闻。"
        else:
            return f"搜索服务暂时不可用 (状态码：{response.status_code})。"
    except Exception as e:
        return f"搜索失败：{str(e)}"

# --- 核心函数：调用 NVIDIA AI ---
def call_nvidia(prompt, model, system_prompt="你是一个有用的助手。", search_context=None):
    if search_context:
        final_prompt = f"请根据以下【最新实时资讯】回答问题，务必体现时效性。\n\n【最新资讯】:\n{search_context}\n\n【用户问题】:\n{prompt}"
    else:
        final_prompt = prompt

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
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
        else:
            return f"❌ AI 服务繁忙 ({response.status_code})。"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"

# --- 主界面 ---
st.title("🌐 小景智能体 (Google News 实时版)")
st.markdown('<p class="subtitle">集成 Google News 实时 RSS + Llama 3.1/Qwen 2.5</p>', unsafe_allow_html=True)

if menu == "📊 智能研报 (Google News)":
    st.header("📊 智能研报生成器")
    st.info("💡 **已开启 Google News 实时搜索**：自动获取过去 48 小时最新新闻。")
    topic = st.text_input("请输入行业或主题")
    if st.button("🚀 开始生成研报"):
        if not topic: st.warning("请输入主题！")
        else:
            with st.spinner(f'🔍 正在抓取 "{topic}" 的最新 Google News...'):
                news = search_google_news(topic)
                if "搜索失败" in news or "不可用" in news:
                    st.warning(f"⚠️ {news} 将使用模型内部知识。")
                    news = None
                
                prompt = f"请作为资深分析师，为'{topic}'写一份研报。要求：1.核心动态 2.关键数据 3.小景建议。结合最新资讯。"
                report = call_nvidia(prompt, MODEL_LLAMA, "你是一位顶级行业分析师。", search_context=news)
                
                if "❌" in report: st.error(report)
                else:
                    st.success("✅ 分析完成！")
                    st.markdown(report)
                    st.download_button("📥 下载报告", report, file_name=f"{topic}_report.md")

elif menu == "📝 会议纪要":
    st.header("📝 会议纪要整理助手")
    raw_text = st.text_area("请粘贴会议记录", height=200)
    if st.button("🪄 一键整理"):
        if not raw_text: st.warning("请输入内容！")
        else:
            with st.spinner('🤖 正在整理...'):
                prompt = f"请整理会议记录：1.核心决策 2.待办事项 3.潜在风险。内容：{raw_text}"
                summary = call_nvidia(prompt, MODEL_QWEN, "你是一位高效的会议秘书。")
                if "❌" in summary: st.error(summary)
                else:
                    st.success("✅ 整理完成！")
                    st.markdown(summary)

elif menu == "🎨 爆款文案 (Google News)":
    st.header("🎨 爆款文案生成器")
    st.info("💡 **已开启 Google News 实时搜索**：结合最新热点生成文案。")
    theme = st.text_input("请输入产品或主题")
    if st.button("✍️ 开始创作"):
        if not theme: st.warning("请输入主题！")
        else:
            with st.spinner(f'🔍 正在抓取 "{theme}" 的最新热点...'):
                news = search_google_news(theme)
                if "搜索失败" in news or "不可用" in news:
                    st.warning(f"⚠️ {news} 将使用模型内部知识。")
                    news = None
                
                prompt = f"请为'{theme}'写 3 个爆款文案（震惊体、专业体、亲切体）。结合最新热点。"
                result = call_nvidia(prompt, MODEL_QWEN, "你是一位新媒体专家。", search_context=news)
                
                if "❌" in result: st.error(result)
                else:
                    st.success("✅ 创作完成！")
                    st.markdown(result)
