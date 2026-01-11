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
st.set_page_config(layout="wide", page_title="Ultimate Stock Metadata Tool")

st.title("🚀 Ultimate Stock Metadata Generator")
st.markdown("เครื่องมือสร้าง Metadata ครบวงจร: เลือกได้ทั้งแบบ **ภาษาสวย (Natural)** หรือ **อัดคีย์เวิร์ด (Stuffer)**")

# --- 🔥 โซนบังคับโชว์ API KEY ---
st.markdown("### 🔑 ตั้งค่า OpenAI API Key (Optional)")
api_key = st.text_input("วาง API Key ของคุณที่นี่ (sk-...) [ใส่เพื่อใช้โหมด AI]", type="password")

if api_key:
    st.success("✅ AI Mode Ready!")
else:
    st.info("ℹ️ Running in Free Mode (Template Based)")
# ------------------------------------------------

st.markdown("---")

ADOBE_CATEGORIES = [
    "1 - Animals", "2 - Architecture", "3 - Business", "4 - Drinks", "5 - Nature",
    "6 - Emotions", "7 - Food", "8 - Graphic", "9 - Hobbies", "10 - Industry",
    "11 - Landscape", "12 - Lifestyle", "13 - People", "14 - Plants", "15 - Culture",
    "16 - Science", "17 - Social Issues", "18 - Sports", "19 - Technology", 
    "20 - Transport", "21 - Travel"
]

# คลังคำกริยา (Action Verbs)
ACTIONS = [
    "using", "holding", "analyzing", "presenting", "working on", 
    "checking", "displaying", "looking at", "reviewing", "preparing",
    "focusing on", "managing", "developing", "creating", "processing"
]

# คำเชื่อมสำหรับ Stuffer Mode
CONNECTORS = [
    "including", "featuring", "related to", "for", "with", "plus", "alongside", "involving", "containing"
]

# --- ฟังก์ชันช่วยเหลือ ---
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
    
    if mode == "A": random.shuffle(head)
    elif mode == "B": random.shuffle(tail)
    elif mode == "C": random.shuffle(head); random.shuffle(tail)
        
    return ", ".join(head + tail)

# --- Logic: Structured / Natural (แบบเดิม) ---
def generate_structured_title(subject, keyword_list):
    """Free Mode: สร้าง Title แบบ Natural (Subject + Action + Object + Context)"""
    forbidden_words = set(re.findall(r'\w+', subject.lower()))
    candidate_keywords = [kw for kw in keyword_list if not (set(re.findall(r'\w+', kw.lower())) & forbidden_words)]
    
    if len(candidate_keywords) < 3:
        return f"{subject} concept with {', '.join(candidate_keywords)}"

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

# --- Logic: Keyword Stuffer (แบบใหม่) ---
def generate_greedy_title(subject, keyword_list):
    """Free Mode: พยายามยัด Keyword ลงไปให้ได้มากที่สุดจนเกือบเต็ม 200 คำ"""
    forbidden_words = set(re.findall(r'\w+', subject.lower()))
    candidate_keywords = [kw for kw in keyword_list if not (set(re.findall(r'\w+', kw.lower())) & forbidden_words)]
    
    # สุ่มลำดับคำที่จะเอามาเติม
    random.shuffle(candidate_keywords)
    
    # เริ่มต้นประโยค
    action = random.choice(ACTIONS)
    base_title = f"{subject} {action}"
    
    # ตัวแปรสำหรับวนลูปเติมคำ
    current_title = base_title
    used_indices = 0
    
    # Loop เติมคำจนกว่าจะเต็ม
    while used_indices < len(candidate_keywords):
        word_to_add = candidate_keywords[used_indices]
        
        # เลือกคำเชื่อม
        connector = ""
        if used_indices == 0:
            connector = f" {random.choice(CONNECTORS)}" # คำแรกต้องมีคำเชื่อม
        elif used_indices % 3 == 0: 
            connector = f" {random.choice(CONNECTORS)}" # ทุก 3 คำเปลี่ยนคำเชื่อม
        else:
            connector = "," # ใช้ลูกน้ำคั่นปกติ
            
        # เช็คความยาว: ถ้าเติมแล้วเกิน 195 ตัวอักษร ให้หยุด
        potential_segment = f"{connector} {word_to_add}"
        if len(current_title) + len(potential_segment) > 195:
            break
            
        current_title += potential_segment
        used_indices += 1
    
    # Clean up
    current_title = current_title.strip(',')
    return current_title[0].upper() + current_title[1:]

# --- AI Generator (รวมศูนย์) ---
def generate_ai_title_unified(client, subject, keyword_list, strategy, model="gpt-4o-mini"):
    try:
        # 1. Strategy: Natural
        if strategy == "Natural":
            sample_kws = ", ".join(random.sample(keyword_list, min(8, len(keyword_list))))
            prompt = f"""
            Write a stock photo title (max 200 chars).
            Structure: Subject ({subject}) + Action (verb) + Object + Context.
            Use keywords: {sample_kws}.
            Style: Natural, Professional, Grammatically correct sentence.
            Return ONLY the title.
            """
            
        # 2. Strategy: Stuffer
        else:
            all_kws_str = ", ".join(keyword_list) # ส่งไปหมดเลย
            prompt = f"""
            Write a Stock Photo Title for subject: "{subject}".
            Goal: Maximize keyword usage up to 200 characters.
            Keywords pool: [{all_kws_str}]
            Constraints:
            - Start with "{subject} [Action]..."
            - Stuff as many keywords as possible.
            - Use connectors (featuring, including, with, for) to make it a valid sentence.
            - NO filler adjectives (e.g. beautiful, amazing).
            - Max length strictly 200 chars.
            Return ONLY the title string.
            """

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- UI Layout ---
with st.form("metadata_form"):
    st.subheader("1. ตั้งค่าการทำงาน")
    
    col1, col2 = st.columns(2)
    with col1:
        # เลือกโหมด AI/Free
        if api_key:
            mode_options = ["🧠 AI Mode (GPT-4o Mini)", "🔥 AI Mode (GPT-4o - ตัวท็อป)", "🆓 Free Mode"]
        else:
            mode_options = ["🆓 Free Mode", "🧠 AI Mode (ต้องใส่ Key ก่อน)"]
        title_mode = st.radio("ระบบประมวลผล (Processing Mode):", mode_options)
        
    with col2:
        # เลือกกลยุทธ์ Title
        strategy = st.radio(
            "กลยุทธ์ Title (Strategy):", 
            ["Balanced / Natural (เน้นภาษาสวย อ่านง่าย)", "Keyword Stuffer (เน้นอัดคีย์เวิร์ดเต็ม 200 คำ)"],
            help="Balanced: เหมาะกับภาพ Portrait/General | Stuffer: เหมาะกับภาพ Business/Concept ที่ต้องการดักคำเยอะๆ"
        )
        strategy_key = "Natural" if "Balanced" in strategy else "Stuffer"

    st.markdown("---")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        subject = st.text_input("Subject / ประธาน (เช่น Asian businessman)", value="Asian businessman")
        selected_category_full = st.selectbox("Adobe Category", ADOBE_CATEGORIES, index=2) 
        category_id = selected_category_full.split(" - ")[0]
        
    with col_input2:
        # Keywords
        raw_keywords = st.text_area("Keywords (สำหรับ Stuffer ควรใส่มาเยอะๆ 20+ คำ)", height=108, 
                                    value="tablet, graph, office, success, growth, 2026, strategy, financial, planning, digital, team, corporate, laptop, wireless, data, analysis, market, investment, report, document")

    st.write("รูปแบบการสุ่ม Keywords (ช่อง Keywords Column):")
    mode_option = st.radio("Rotation Mode", ["A: สลับ 10 คำแรก", "B: ล็อค 10 คำแรก", "C: สลับหมด"], horizontal=True)
    selected_mode = mode_option.split(":")[0]

    st.markdown("---")
    num_rows = st.slider("จำนวนรูป (Rows)", 1, 100, 100)
    submitted = st.form_submit_button(f"🚀 Generate CSV ({num_rows} Rows)")

# --- Processing ---
if submitted:
    if not subject or not raw_keywords:
        st.error("กรุณาใส่ข้อมูลให้ครบก่อนครับ")
    elif "AI Mode" in title_mode and not api_key:
        st.error("⛔️ เลือกโหมด AI แต่ลืมใส่ Key ด้านบนครับ!")
    else:
        keyword_list = clean_keyword_list(raw_keywords)
        client = None
        
        if "AI Mode" in title_mode:
            if not OPENAI_AVAILABLE:
                st.error("❌ เครื่องคุณยังไม่มี openai library!")
                st.stop()
            client = OpenAI(api_key=api_key)

        model_name = "gpt-4o-mini"
        if "GPT-4o" in title_mode: model_name = "gpt-4o"

        progress_bar = st.progress(0)
        data_rows = []
        
        for i in range(1, num_rows + 1):
            progress_bar.progress(i / num_rows)
            filename = f"custom-{i:02d}.jpg"
            
            # Keywords Column
            kw_str = generate_shuffled_keywords(keyword_list[:], selected_mode)
            
            # Title Generation
            if "AI Mode" in title_mode:
                final_title = generate_ai_title_unified(client, subject, keyword_list, strategy_key, model=model_name)
            else:
                if strategy_key == "Stuffer":
                    final_title = generate_greedy_title(subject, keyword_list)
                else:
                    final_title = generate_structured_title(subject, keyword_list)
            
            data_rows.append({
                "Filename": filename, "Title": final_title, 
                "Keywords": kw_str, "Category": category_id, "Releases": "no"
            })
            
        df = pd.DataFrame(data_rows)
        st.success(f"✅ เสร็จสิ้น! (Mode: {title_mode} | Strategy: {strategy_key})")
        
        # Preview Title Length
        df['Len'] = df['Title'].apply(len)
        st.dataframe(df[['Title', 'Len']].head())
        
        df_download = df.drop(columns=['Len'])
        st.download_button("💾 Download CSV", df_download.to_csv(index=False, quotechar='"', quoting=1), "ultimate_metadata.csv", "text/csv", type="primary")