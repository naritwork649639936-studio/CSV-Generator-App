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
st.set_page_config(layout="wide", page_title="Structured Stock Metadata Tool (FINAL FIXED)")

st.title("🚀 Structured Stock Photo Metadata Generator")

# --- 🔥 โซนบังคับโชว์ API KEY (อยู่บนสุด) ---
st.markdown("### 🔑 ตั้งค่า OpenAI API Key")
api_key = st.text_input("วาง API Key ของคุณที่นี่ (sk-...)", type="password", help="ใส่เพื่อใช้โหมด AI ถ้าไม่ใส่ให้ใช้โหมดฟรี")

if api_key:
    st.success("✅ รับทราบ API Key แล้ว! คุณสามารถเลือกโหมด AI ด้านล่างได้เลย")
else:
    st.info("ℹ️ ยังไม่ใส่ Key -> ระบบจะทำงานในโหมด Free Template เท่านั้น")
# ------------------------------------------------

st.markdown("---")

# --- ส่วนข้อมูลสำหรับ UI ---
ADOBE_CATEGORIES = [
    "1 - Animals", "2 - Architecture", "3 - Business", "4 - Drinks", "5 - Nature",
    "6 - Emotions", "7 - Food", "8 - Graphic", "9 - Hobbies", "10 - Industry",
    "11 - Landscape", "12 - Lifestyle", "13 - People", "14 - Plants", "15 - Culture",
    "16 - Science", "17 - Social Issues", "18 - Sports", "19 - Technology", 
    "20 - Transport", "21 - Travel"
]

ACTIONS = [
    "using", "holding", "analyzing", "presenting", "working on", 
    "checking", "displaying", "looking at", "reviewing", "preparing",
    "focusing on", "managing", "developing", "creating"
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

def generate_structured_title(subject, keyword_list):
    """Free Mode Logic"""
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

def generate_ai_title(client, subject, keyword_list, model="gpt-4o-mini"):
    """AI Mode Logic"""
    try:
        sample_kws = ", ".join(random.sample(keyword_list, min(8, len(keyword_list))))
        prompt = f"""Write a stock photo title (max 200 chars) using this structure: Subject ({subject}) + Action (verb) + Object (from keywords) + Context/Place. Keywords pool: {sample_kws}. Make it natural. Return ONLY title."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip().replace('"', '')
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- UI Layout ---
with st.form("metadata_form"):
    st.subheader("1. เลือกโหมด & หมวดหมู่")
    
    col_mode, col_cat = st.columns([1, 1])
    with col_mode:
        # --- ปรับปรุงตรงนี้: เพิ่มตัวเลือก Model กลับมาแล้ว ---
        mode_options = [
            "🆓 Free Mode (Template)", 
            "🧠 AI Mode (GPT-4o Mini) - ประหยัด", 
            "🔥 AI Mode (GPT-4o) - ตัวท็อป"
        ]
        title_mode = st.radio("ระบบสร้าง Title:", mode_options)
    
    with col_cat:
        selected_category_full = st.selectbox("Adobe Category", ADOBE_CATEGORIES, index=2) 
        category_id = selected_category_full.split(" - ")[0]

    st.markdown("---")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        subject = st.text_input("Subject / ประธาน (เช่น Asian businessman)", value="Asian businessman")
    
    st.subheader("2. จัดการ Keywords")
    raw_keywords = st.text_area("Keywords (Object & Context)", height=150, value="tablet, graph, office, success, growth, 2026, strategy, financial")
    
    st.write("รูปแบบการสุ่ม Keywords:")
    mode_option = st.radio("Mode Selection", ["A: สลับ 10 คำแรก", "B: ล็อค 10 คำแรก", "C: สลับหมด"])
    selected_mode = mode_option.split(":")[0]

    st.markdown("---")
    num_rows = st.slider("จำนวนรูป (Rows)", 1, 100, 100)
    submitted = st.form_submit_button(f"🚀 Generate CSV ({num_rows} Rows)")

# --- Processing ---
if submitted:
    if not subject or not raw_keywords:
        st.error("กรุณาใส่ข้อมูลให้ครบก่อนครับ")
    # เช็คว่าเลือก AI Mode แต่ลืมใส่ Key หรือไม่
    elif "AI Mode" in title_mode and not api_key:
        st.error("⛔️ คุณเลือกโหมด AI แต่ยังไม่ใส่ API Key ด้านบนครับ! กรุณาใส่ Key หรือเปลี่ยนเป็น Free Mode")
    else:
        keyword_list = clean_keyword_list(raw_keywords)
        client = None
        
        # Setup AI Client
        if "AI Mode" in title_mode:
            if not OPENAI_AVAILABLE:
                st.error("❌ เครื่องคุณยังไม่มี openai library! (pip install openai)")
                st.stop()
            client = OpenAI(api_key=api_key)

        # Select Model based on user choice
        model_name = "gpt-4o-mini" # default
        if "GPT-4o" in title_mode:
            model_name = "gpt-4o"

        progress_bar = st.progress(0)
        data_rows = []
        
        for i in range(1, num_rows + 1):
            progress_bar.progress(i / num_rows)
            filename = f"custom-{i:02d}.jpg"
            
            # Keywords
            kw_str = generate_shuffled_keywords(keyword_list[:], selected_mode)
            
            # Title
            if "AI Mode" in title_mode:
                final_title = generate_ai_title(client, subject, keyword_list, model=model_name)
            else:
                final_title = generate_structured_title(subject, keyword_list)
            
            data_rows.append({
                "Filename": filename, "Title": final_title, 
                "Keywords": kw_str, "Category": category_id, "Releases": "no"
            })
            
        df = pd.DataFrame(data_rows)
        st.success(f"✅ เสร็จแล้วครับ! (ใช้โหมด: {title_mode})")
        st.dataframe(df.head())
        
        st.download_button("💾 Download CSV", df.to_csv(index=False, quotechar='"', quoting=1), "final_metadata.csv", "text/csv", type="primary")