import streamlit as st
import requests
import time
import json

# --- 1. 配置区域 (NVIDIA API) ---
API_KEY = "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"
BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# 模型定义
MODEL_LLAMA = "meta/llama-3.1-405b-instruct" # 研报专用 (最强逻辑)
MODEL_QWEN = "qwen/qwen2.5-72b-instruct"    # 纪要/文案专用 (最强中文)

# --- 2. 页面配置 ---
st.set_page_config(
    page_title="小景智能体科技 | NVIDIA 最强版",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. 自定义 CSS ---
st.markdown("""
<style>
.stApp { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
h1 { color: #4f46e5; font-weight: 800; text-align: center; }
.subtitle { text-align: center; color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem; }
.stButton>button {
    background-color: #76b900; /* NVIDIA 绿 */
    color: white;
    border-radius: 6px;
    font-weight: 600;
    border: none;
    width: 100%;
    font-size: 1.1rem;
}
.stButton>button:hover { background-color: #5a8f00; box-shadow: 0 4px 6px rgba(118, 185, 0, 0.3); }
</style>
""", unsafe_allow_html=True)

# --- 4. 侧边栏 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("小景智能体")
    st.markdown("**让 AI 成为你的超级员工**")
    st.divider()
    menu = st.radio(
        "选择功能",
        ["📊 智能研报生成", "📝 会议纪要助手", "🎨 爆款文案工厂"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("© 2026 小景智能体科技")
    st.markdown("[联系我们要定制服务](mailto:contact@xiaojing.ai)")

# --- 5. AI 核心函数 (NVIDIA API) ---
def call_nvidia(prompt, model, system_prompt="你是一个有用的助手。"):
    """调用 NVIDIA API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1,
        "stream": False
    }
    
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        elif response.status_code == 401:
            return "❌ 认证失败：API Key 无效，请检查代码。"
        elif response.status_code == 429:
            return "⚠️ 请求过快：请稍微慢一点点再试。"
        else:
            return f"⚠️ 服务暂时繁忙 (状态码：{response.status_code})，请稍后重试。\n错误信息：{response.text[:200]}"
    except Exception as e:
        return f"❌ 网络请求失败：{str(e)}"

# --- 6. 主界面逻辑 ---
st.title("🤖 小景智能体工作台 (NVIDIA 最强版)")
st.markdown('<p class="subtitle">双核驱动：Llama 3.1 405B (逻辑) + Qwen 2.5 72B (中文)</p>', unsafe_allow_html=True)

if menu == "📊 智能研报生成":
    st.header("📊 智能研报生成器")
    st.info("💡 使用 **Llama 3.1 405B** 地表最强模型，深度分析行业趋势。")
    topic = st.text_input("请输入你关注的行业或主题 (例如：AI Agent, 新能源, 跨境电商)")
    
    if st.button("🚀 开始生成研报", use_container_width=True):
        if not topic:
            st.warning("请先输入主题！")
        else:
            with st.spinner(f'🤖 Llama 3.1 405B 正在深度分析 "{topic}" ...'):
                prompt = f"请作为一位资深行业分析师，为'{topic}'写一份简短但专业的行业研报。要求：1. 核心动态 (3 点) 2. 关键数据 (3 个) 3. 小景建议 (3 条)。请使用 Markdown 格式，语言简练有力。"
                report = call_nvidia(prompt, MODEL_LLAMA, "你是一位拥有 20 年经验的顶级行业分析师，擅长洞察市场趋势。")
                
                if "⚠️" in report or "❌" in report:
                    st.error(report)
                else:
                    st.success("✅ 分析完成！")
                    st.markdown(report)
                    st.download_button("📥 下载报告 (Markdown)", report, file_name=f"{topic}_report.md", use_container_width=True)

elif menu == "📝 会议纪要助手":
    st.header("📝 会议纪要整理助手")
    st.info("💡 使用 **Qwen 2.5 72B** 中文最强模型，精准提取待办事项。")
    raw_text = st.text_area("请粘贴混乱的会议记录:", height=200, placeholder="大家下午好，我们简单过一下这个项目...")
    
    if st.button("🪄 一键整理", use_container_width=True):
        if not raw_text:
            st.warning("请先粘贴内容！")
        else:
            with st.spinner('🤖 Qwen 2.5 正在提炼核心信息...'):
                prompt = f"请整理以下会议记录，提取：1. 核心决策 (列表) 2. 待办事项 (To-Do 列表，含负责人和截止时间如果有) 3. 潜在风险。输出为清晰的 Markdown 格式。\n\n会议记录内容：{raw_text}"
                summary = call_nvidia(prompt, MODEL_QWEN, "你是一位高效、严谨的会议秘书，擅长从杂乱信息中提炼重点。")
                
                if "⚠️" in summary or "❌" in summary:
                    st.error(summary)
                else:
                    st.success("✅ 整理完成！")
                    st.markdown(summary)
                    st.code(summary, language="text", line_numbers=True)

elif menu == "🎨 爆款文案工厂":
    st.header("🎨 爆款文案生成器")
    st.info("💡 使用 **Qwen 2.5 72B** 中文最强模型，写出接地气的爆款文案。")
    theme = st.text_input("请输入产品或主题 (例如：2026 年普通人如何用 AI 搞钱)")
    
    if st.button("✍️ 开始创作", use_container_width=True):
        if not theme:
            st.warning("请输入主题！")
        else:
            with st.spinner(f'🤖 Qwen 2.5 正在构思 "{theme}" 的爆款文案...'):
                prompt = f"请为'{theme}'写 3 个不同风格的爆款文案（震惊体、专业体、亲切体）。每个风格包含：1. 标题 (吸引人) 2. 正文 (带 Emoji，口语化) 3. 推荐标签。请使用 Markdown 格式。"
                result = call_nvidia(prompt, MODEL_QWEN, "你是一位拥有百万粉丝的新媒体运营专家，擅长撰写各种风格的爆款文案。")
                
                if "⚠️" in result or "❌" in result:
                    st.error(result)
                else:
                    st.success("✅ 创作完成！")
                    st.markdown(result)
                    st.code(result, language="text")

# --- 7. 页脚 ---
st.divider()
st.markdown("<div style='text-align: center; color: #9ca3af; font-size: 0.8rem;'>Powered by XiaoJing Agent Tech | NVIDIA NIM (Llama 3.1 & Qwen 2.5)</div>", unsafe_allow_html=True)
