import streamlit as st
import requests
import time
import os
from duckduckgo_search import DDGS

# ================= 配置区域 =================
# 【安全】从 Streamlit Secrets (TOML) 读取 NVIDIA API Key
try:
    API_KEY = st.secrets["nvidia"]["api_key"]
except KeyError:
    st.error("⚠️ 严重错误：未在 secrets.toml 中找到 NVIDIA 密钥！请检查 Streamlit 后台配置。")
    st.stop()

BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# 模型定义
MODEL_LLAMA = "meta/llama-3.1-405b-instruct"  # 研报专用 (最强逻辑)
MODEL_QWEN = "qwen/qwen2.5-72b-instruct"      # 纪要/文案专用 (最强中文)
# ==========================================

# --- 页面配置 ---
st.set_page_config(
    page_title="小景智能体科技 | NVIDIA 安全版",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自定义 CSS ---
st.markdown("""
<style>
.stApp { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
h1 { color: #4f46e5; font-weight: 800; text-align: center; }
.subtitle { text-align: center; color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem; }
.stButton>button {
    background-color: #76b900; /* NVIDIA 绿 */
    color: white; border-radius: 6px; font-weight: 600; border: none; width: 100%; font-size: 1.1rem;
}
.stButton>button:hover { background-color: #5a8f00; box-shadow: 0 4px 6px rgba(118, 185, 0, 0.3); }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("小景智能体")
    st.markdown("**让 AI 成为你的超级员工**")
    st.divider()
    menu = st.radio(
        "选择功能",
        ["📊 智能研报生成 (联网)", "📝 会议纪要助手", "🎨 爆款文案工厂 (联网)"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("© 2026 小景智能体科技")
    st.markdown("[联系我们要定制服务](mailto:contact@xiaojing.ai)")

# --- 核心函数：联网搜索 ---
def search_web(query, num_results=5):
    """使用 DuckDuckGo 搜索最新新闻"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            if not results:
                return "未找到相关搜索结果。"
            context = "以下是最新的网络搜索结果：\n\n"
            for i, r in enumerate(results):
                context += f"{i+1}. **{r['title']}** ({r['href']})\n{ r['body']}\n\n"
            return context
    except Exception as e:
        return f"搜索失败：{str(e)}"

# --- 核心函数：调用 NVIDIA AI ---
def call_nvidia(prompt, model, system_prompt="你是一个有用的助手。", search_query=None):
    """调用 NVIDIA API (带联网搜索增强)"""
    final_prompt = prompt
    search_context = ""

    # 如果需要联网搜索
    if search_query:
        with st.spinner("🌐 正在全网搜索最新资讯..."):
            search_context = search_web(search_query)
            if "搜索失败" in search_context:
                st.warning("⚠️ 联网搜索失败，将使用模型内部知识。")
                search_context = ""
            else:
                st.success("✅ 已获取最新网络资讯，正在分析...")

    # 构建增强 Prompt
    if search_context:
        final_prompt = f"""
请根据以下【最新网络资讯】回答问题。
注意：资讯可能包含时间、地点、数据，请务必引用最新资讯中的内容，确保时效性。

【最新网络资讯】:
{search_context}

【用户问题】:
{prompt}
"""
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
        "max_tokens": 1024,
        "temperature": 0.7,
        "stream": False
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        elif response.status_code == 401:
            return "❌ 认证失败：API Key 无效。"
        else:
            return f"⚠️ 服务繁忙 ({response.status_code})，请稍后重试。"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"

# --- 主界面逻辑 ---
st.title("🌐 小景智能体工作台 (NVIDIA 安全版)")
st.markdown('<p class="subtitle">集成 DuckDuckGo 实时搜索 + Llama 3.1/Qwen 2.5 双核驱动 | 密钥已加密存储</p>', unsafe_allow_html=True)

if menu == "📊 智能研报生成 (联网)":
    st.header("📊 智能研报生成器")
    st.info("💡 **已开启联网模式**：将自动搜索最新行业新闻、股价、政策，生成为止最鲜活的研报。")
    topic = st.text_input("请输入你关注的行业或主题 (例如：2026 年 AI 最新进展)")
    if st.button("🚀 开始生成研报 (联网)", use_container_width=True):
        if not topic:
            st.warning("请先输入主题！")
        else:
            search_q = f"{topic} news 2026 latest trends stock price"
            with st.spinner(f'🔍 正在搜索 "{topic}" 的最新资讯...'):
                prompt = f"请作为一位资深行业分析师，为'{topic}'写一份简短但专业的行业研报。要求：1. 核心动态 (结合最新新闻) 2. 关键数据 3. 小景建议。请使用 Markdown 格式。"
                report = call_nvidia(prompt, MODEL_LLAMA, "你是一位拥有 20 年经验的顶级行业分析师，擅长结合最新数据洞察市场趋势。", search_query=search_q)
                if "⚠️" in report or "❌" in report:
                    st.error(report)
                else:
                    st.success("✅ 分析完成！(基于最新数据)")
                    st.markdown(report)
                    st.download_button("📥 下载报告", report, file_name=f"{topic}_report.md", use_container_width=True)

elif menu == "📝 会议纪要助手":
    st.header("📝 会议纪要整理助手")
    st.info("💡 此功能无需联网，专注于整理内部记录。")
    raw_text = st.text_area("请粘贴混乱的会议记录:", height=200)
    if st.button("🪄 一键整理", use_container_width=True):
        if not raw_text:
            st.warning("请先粘贴内容！")
        else:
            with st.spinner('🤖 Qwen 2.5 正在提炼核心信息...'):
                prompt = f"请整理以下会议记录，提取：1. 核心决策 2. 待办事项 3. 潜在风险。输出为 Markdown。内容：{raw_text}"
                summary = call_nvidia(prompt, MODEL_QWEN, "你是一位高效、严谨的会议秘书。")
                if "⚠️" in summary or "❌" in summary:
                    st.error(summary)
                else:
                    st.success("✅ 整理完成！")
                    st.markdown(summary)
                    st.code(summary, language="text")

elif menu == "🎨 爆款文案工厂 (联网)":
    st.header("🎨 爆款文案生成器")
    st.info("💡 **已开启联网模式**：将自动搜索该主题下的最新热点、流行语，生成最蹭热点的文案。")
    theme = st.text_input("请输入产品或主题 (例如：2026 年 AI 搞钱)")
    if st.button("✍️ 开始创作 (联网)", use_container_width=True):
        if not theme:
            st.warning("请输入主题！")
        else:
            search_q = f"{theme} trending topics 2026 memes hot words"
            with st.spinner(f'🔍 正在搜索 "{theme}" 的最新热点...'):
                prompt = f"请为'{theme}'写 3 个不同风格的爆款文案（震惊体、专业体、亲切体）。结合最新热点和流行语。每个包含标题、正文 (带 Emoji)、标签。"
                result = call_nvidia(prompt, MODEL_QWEN, "你是一位拥有百万粉丝的新媒体运营专家，擅长蹭热点。", search_query=search_q)
                if "⚠️" in result or "❌" in result:
                    st.error(result)
                else:
                    st.success("✅ 创作完成！(结合最新热点)")
                    st.markdown(result)
                    st.code(result, language="text")

# --- 页脚 ---
st.divider()
st.markdown("<div style='text-align: center; color: #9ca3af; font-size: 0.8rem;'>Powered by XiaoJing Agent Tech | NVIDIA NIM + DuckDuckGo Search</div>", unsafe_allow_html=True)
