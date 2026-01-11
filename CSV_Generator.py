import streamlit as st
import pandas as pd
import random
import re

# พยายาม Import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ตั้งค่าหน้าเว็บ
st.set_page_config(layout="wide", page_title="Ultimate Metadata Tool (Fixed UI)")

st.title("🚀 Ultimate Stock Metadata Generator")
st.markdown("เครื่องมือสร้าง Metadata ครบวงจร (Free & AI)")
st.markdown("---")

# ==========================================
# 1. ส่วนตั้งค่า API KEY (อยู่บนสุด)
# ==========================================
st.header("🔑 1. ตั้งค่า OpenAI API Key")
api_key = st.text_input("API Key (sk-...) [ใส่เพื่อใช้โหมด AI]", type="password")
if api_key:
    st.success("✅ Connect OpenAI เรียบร้อย")
else:
    st.info("ℹ️ ถ้าไม่ใส่ Key ระบบจะรันได้แค่ Free Mode")

st.markdown("---")

# ==========================================
# 2. ส่วนตั้งค่าโหมด (แยกชัดเจน ไม่ซ่อน)
# ==========================================
with st.form("metadata_form"):
    st.header("⚙️ 2. ตั้งค่าระบบ (Settings)")
    
    # 2.1 เลือกโหมดหลัก (Main System)
    st.subheader("🅰️ เลือกระบบทำงาน (Operation Mode)")
    system_mode = st.radio(
        "เลือกโหมด:",
        ["🆓 Free Mode (ใช้ Template ฟรี)", "🧠 AI Mode (ใช้ ChatGPT คิดให้)"],
        horizontal=True
    )

    # 2.2 เลือก Model (จะโชว์ก็ต่อเมื่อเลือก AI Mode หรือโชว์ไปเลยก็ได้เพื่อความชัวร์)
    # เพื่อความชัดเจน ผมโชว์ให้เห็นเลยแต่ Disable ถ้าไม่ได้เลือก AI
    st.subheader("🅱️ เลือกโมเดล AI (AI Model)")
    ai_model_select = st.radio(
        "เลือกความฉลาด (ถ้าใช้โหมด AI):",
        ["GPT-4o Mini (ประหยัด/เร็ว)", "GPT-4o (ตัวท็อป/ฉลาดสุด)"],
        horizontal=True
    )
    
    # 2.3 เลือก Strategy
    st.subheader("🆎 เลือกกลยุทธ์ Title (Strategy)")
    strategy = st.radio(
        "ต้องการ Title สไตล์ไหน?", 
        ["Balanced / Natural (เน้นภาษาสวย อ่านง่าย)", "Keyword Stuffer (เน้นอัดคีย์เวิร์ดเต็ม 200 คำ)"],
        horizontal=True
    )
    strategy_key = "Natural" if "Balanced" in strategy else "Stuffer"

    st.markdown("---")
    
    # ==========================================
    # 3. ส่วนข้อมูลภาพ (Input)
    # ==========================================
    st.header("📝 3. ข้อมูลภาพ (Inputs)")
    
    col_sub, col_cat = st.columns(2)
    with col_sub:
        subject = st.text_input("Subject / ประธาน (เช่น Asian businessman)", value="Asian businessman")
    with col_cat:
        # Categories
        ADOBE_CATEGORIES = [
            "1 - Animals", "2 - Architecture", "3 - Business", "4 - Drinks", "5 - Nature",
            "6 - Emotions", "7 - Food", "8 - Graphic", "9 - Hobbies", "10 - Industry",
            "11 - Landscape", "12 - Lifestyle", "13 - People", "14 - Plants", "15 - Culture",
            "16 - Science", "17 - Social Issues", "18 - Sports", "19 - Technology", 
            "20 - Transport", "21 - Travel"
        ]
        selected_category_full = st.selectbox("Adobe Category", ADOBE_CATEGORIES, index=2) 
        category_id = selected_category_full.split(" - ")[0]
        
    raw_keywords = st.text_area("Keywords (ใส่ 20-49 คำ)", height=150, 
                                value="tablet, graph, office, success, growth, 2026, strategy, financial, planning, digital, team, corporate, laptop, wireless, data, analysis, market, investment, report, document")

    # ==========================================
    # 4. Keyword Rotation (ข้อความตามสั่ง)
    # ==========================================
    st.subheader("🔄 รูปแบบการสุ่ม Keywords (Rotation)")
    mode_option = st.radio(
        "เลือกรูปแบบการกระจายคำ:", 
        [
            "Mode A: สลับ 10 คำแรก (1-10) / ล็อคส่วนหลัง (11+)", 
            "Mode B: ล็อค 10 คำแรก (1-10) / สลับส่วนหลัง (11+)", 
            "Mode C: สลับทั้งหมด (กระจายความเสี่ยงสูงสุด)"
        ]
    )
    # Logic การตัด string เพื่อเอา A, B, C
    if "Mode A" in mode_option: selected_mode = "A"
    elif "Mode B" in mode_option: selected_mode = "B"
    else: selected_mode = "C"

    st.markdown("---")
    num_rows = st.slider("จำนวนรูป (Rows)", 1, 100, 100)
    submitted = st.form_submit_button(f"🚀 Generate CSV ({num_rows} Rows)")

# ==========================================
# Processing Logic
# ==========================================

ACTIONS = [
    "using", "holding", "analyzing", "presenting", "working on", 
    "checking", "displaying", "looking at", "reviewing", "preparing",
    "focusing on", "managing", "developing", "creating", "processing"
]
CONNECTORS = ["including", "featuring", "related to", "for", "with", "plus", "alongside", "involving", "containing"]

def clean_keyword_list(text):
    if not text: return []
    words = [w.strip() for w in text.split(',')]
    return [w for w in words if w]

def generate_shuffled_keywords(keywords, mode):
    if not keywords: return ""
    if len(keywords) < 10:
        temp = keywords[:]
        random.shuffle(temp)
        return ", ".join(temp)
    
    head = keywords[:10]
    tail = keywords[10:]
    
    if mode == "A": 
        random.shuffle(head)
    elif mode == "B": 
        random.shuffle(tail)
    elif mode == "C": 
        random.shuffle(head)
        random.shuffle(tail)
        
    return ", ".join(head + tail)

# Logic Generators
def generate_structured_title(subject, keyword_list):
    """Free Mode: Natural"""
    forbidden_words = set(re.findall(r'\w+', subject.lower()))
    candidate_keywords = [kw for kw in keyword_list if not (set(re.findall(r'\w+', kw.lower())) & forbidden_words)]
    if len(candidate_keywords) < 3: return f"{subject} concept with {', '.join(candidate_keywords)}"
    action = random.choice(ACTIONS)
    picks = random.sample(candidate_keywords, 3)
    obj1, obj2, context = picks[0], picks[1], picks[2]
    templates = [
        f"{subject} {action} {obj1} and {obj2} in {context} setting",
        f"{subject} {action} {obj1} for {obj2} concept",
        f"{subject} {action} {obj1} with {obj2} in background",
        f"Concept of {subject} {action} {obj1} related to {context}",
        f"{subject} in {context} {action} {obj1} and {obj2}",
        f"Professional {subject} {action} {obj1} for {context} strategy",
        f"{obj1} and {obj2} being {action} by {subject} in {context}",
        f"{subject} dedicated to {action} {obj1} for {context} success"
    ]
    return random.choice(templates).capitalize()

def generate_greedy_title(subject, keyword_list):
    """Free Mode: Stuffer"""
    forbidden_words = set(re.findall(r'\w+', subject.lower()))
    candidate_keywords = [kw for kw in keyword_list if not (set(re.findall(r'\w+', kw.lower())) & forbidden_words)]
    random.shuffle(candidate_keywords)
    action = random.choice(ACTIONS)
    base_title = f"{subject} {action}"
    current_title = base_title
    used_indices = 0
    while used_indices < len(candidate_keywords):
        word_to_add = candidate_keywords[used_indices]
        connector = ""
        if used_indices == 0: connector = f" {random.choice(CONNECTORS)}"
        elif used_indices % 3 == 0: connector = f" {random.choice(CONNECTORS)}"
        else: connector = "," 
        potential_segment = f"{connector} {word_to_add}"
        if len(current_title) + len(potential_segment) > 195: break
        current_title += potential_segment
        used_indices += 1
    return current_title.strip(',')[0].upper() + current_title.strip(',')[1:]

def generate_ai_title_unified(client, subject, keyword_list, strategy, model_choice):
    try:
        model = "gpt-4o-mini"
        if "GPT-4o (ตัวท็อป" in model_choice: model = "gpt-4o"

        if strategy == "Natural":
            sample_kws = ", ".join(random.sample(keyword_list, min(8, len(keyword_list))))
            prompt = f"Write a stock photo title (max 200 chars). Structure: Subject ({subject}) + Action (verb) + Object + Context. Use keywords: {sample_kws}. Style: Natural, Professional. Return ONLY title."
        else:
            all_kws_str = ", ".join(keyword_list)
            prompt = f"Write a Stock Photo Title for subject: \"{subject}\". Goal: Maximize keyword usage up to 200 characters. Keywords pool: [{all_kws_str}]. Start with \"{subject} [Action]...\". Stuff keywords using connectors. Max 200 chars. Return ONLY title."

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        return f"AI Error: {str(e)}"

if submitted:
    if not subject or not raw_keywords:
        st.error("กรุณาใส่ข้อมูลให้ครบก่อนครับ")
    elif "AI Mode" in system_mode and not api_key:
        st.error("⛔️ เลือกโหมด AI แต่ลืมใส่ Key ด้านบนครับ!")
    else:
        keyword_list = clean_keyword_list(raw_keywords)
        client = None
        if "AI Mode" in system_mode:
            if not OPENAI_AVAILABLE:
                st.error("❌ เครื่องคุณยังไม่มี openai library!")
                st.stop()
            client = OpenAI(api_key=api_key)

        progress_bar = st.progress(0)
        data_rows = []
        
        for i in range(1, num_rows + 1):
            progress_bar.progress(i / num_rows)
            filename = f"custom-{i:02d}.jpg"
            kw_str = generate_shuffled_keywords(keyword_list[:], selected_mode)
            
            if "AI Mode" in system_mode:
                final_title = generate_ai_title_unified(client, subject, keyword_list, strategy_key, ai_model_select)
            else:
                if strategy_key == "Stuffer":
                    final_title = generate_greedy_title(subject, keyword_list)
                else:
                    final_title = generate_structured_title(subject, keyword_list)
            
            data_rows.append({"Filename": filename, "Title": final_title, "Keywords": kw_str, "Category": category_id, "Releases": "no"})
            
        df = pd.DataFrame(data_rows)
        st.success("✅ เสร็จสิ้น!")
        df['Len'] = df['Title'].apply(len)
        st.dataframe(df[['Title', 'Len']].head())
        df_download = df.drop(columns=['Len'])
        st.download_button("💾 Download CSV", df_download.to_csv(index=False, quotechar='"', quoting=1), "ultimate_metadata_fixed.csv", "text/csv", type="primary")