import streamlit as st
import requests
import time
import json

# --- 1. 配置区域 ---
# 使用 Hugging Face 免费公开接口 (模型：Qwen2.5-72B-Instruct)
API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"
HEADERS = {"Content-Type": "application/json"}

# --- 2. 页面配置 ---
st.set_page_config(
    page_title="小景智能体科技 | 真实 AI 版",
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
    background-color: #4f46e5; color: white; border-radius: 6px;
    font-weight: 600; border: none; width: 100%;
}
.stButton>button:hover { background-color: #4338ca; box-shadow: 0 4px 6px rgba(79, 70, 229, 0.3); }
.stTextInput>div>div>input { border: 1px solid #d1d5db; border-radius: 6px; }
.stTextArea>div>div>textarea { border: 1px solid #d1d5db; border-radius: 6px; }
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

# --- 5. AI 核心函数 (带重试机制) ---
def call_ai(prompt, system_prompt="你是一个有用的助手。"):
    """调用 Hugging Face 免费接口，带简单重试"""
    # 构建 Qwen 格式的 Prompt
    full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "return_full_text": False,
            "do_sample": True
        }
    }
    
    try:
        # 第一次请求
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        
        # 如果模型正在加载 (503)，等待 2 秒重试一次
        if response.status_code == 503:
            time.sleep(2)
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
            
        if response.status_code == 200:
            result = response.json()[0]['generated_text']
            return result
        else:
            return f"⚠️ 服务暂时繁忙 (状态码: {response.status_code})，请稍后重试。\n错误信息：{response.text[:100]}"
    except Exception as e:
        return f"❌ 网络请求失败：{str(e)}"

# --- 6. 主界面逻辑 ---
st.title("🤖 小景智能体工作台 (真实 AI 增强版)")
st.markdown('<p class="subtitle">基于 Qwen2.5-72B 大模型，三核驱动，真实智能。</p>', unsafe_allow_html=True)

if menu == "📊 智能研报生成":
    st.header("📊 智能研报生成器")
    topic = st.text_input("请输入你关注的行业或主题 (例如：AI Agent, 新能源, 跨境电商)")
    
    if st.button("🚀 开始生成研报", use_container_width=True):
        if not topic:
            st.warning("请先输入主题！")
        else:
            with st.spinner(f'🤖 AI 正在全网检索并深度分析 "{topic}" ...'):
                prompt = f"请作为一位资深行业分析师，为'{topic}'写一份简短但专业的行业研报。要求：1. 核心动态 (3点) 2. 关键数据 (3个) 3. 小景建议 (3条)。请使用 Markdown 格式，语言简练有力。"
                report = call_ai(prompt, "你是一位拥有 20 年经验的顶级行业分析师，擅长洞察市场趋势。")
                
                if "⚠️" in report or "❌" in report:
                    st.error(report)
                else:
                    st.success("✅ 分析完成！")
                    st.markdown(report)
                    st.download_button("📥 下载报告 (Markdown)", report, file_name=f"{topic}_report.md", use_container_width=True)

elif menu == "📝 会议纪要助手":
    st.header("📝 会议纪要整理助手")
    raw_text = st.text_area("请粘贴混乱的会议记录:", height=200, placeholder="大家下午好，我们简单过一下这个项目...")
    
    if st.button("🪄 一键整理", use_container_width=True):
        if not raw_text:
            st.warning("请先粘贴内容！")
        else:
            with st.spinner('🤖 AI 正在提炼核心信息...'):
                prompt = f"请整理以下会议记录，提取：1. 核心决策 (列表) 2. 待办事项 (To-Do 列表，含负责人和截止时间如果有) 3. 潜在风险。输出为清晰的 Markdown 格式。\n\n会议记录内容：{raw_text}"
                summary = call_ai(prompt, "你是一位高效、严谨的会议秘书，擅长从杂乱信息中提炼重点。")
                
                if "⚠️" in summary or "❌" in summary:
                    st.error(summary)
                else:
                    st.success("✅ 整理完成！")
                    st.markdown(summary)
                    st.code(summary, language="text", line_numbers=True)

elif menu == "🎨 爆款文案工厂":
    st.header("🎨 爆款文案生成器")
    theme = st.text_input("请输入产品或主题 (例如：2026 年普通人如何用 AI 搞钱)")
    
    if st.button("✍️ 开始创作", use_container_width=True):
        if not theme:
            st.warning("请输入主题！")
        else:
            with st.spinner(f'🤖 AI 正在构思 "{theme}" 的爆款文案...'):
                prompt = f"请为'{theme}'写 3 个不同风格的爆款文案（震惊体、专业体、亲切体）。每个风格包含：1. 标题 (吸引人) 2. 正文 (带 Emoji，口语化) 3. 推荐标签。请使用 Markdown 格式。"
                result = call_ai(prompt, "你是一位拥有百万粉丝的新媒体运营专家，擅长撰写各种风格的爆款文案。")
                
                if "⚠️" in result or "❌" in result:
                    st.error(result)
                else:
                    st.success("✅ 创作完成！")
                    st.markdown(result)
                    st.code(result, language="text")

# --- 7. 页脚 ---
st.divider()
st.markdown("<div style='text-align: center; color: #9ca3af; font-size: 0.8rem;'>Powered by XiaoJing Agent Tech | Hugging Face Qwen2.5-72B</div>", unsafe_allow_html=True)
