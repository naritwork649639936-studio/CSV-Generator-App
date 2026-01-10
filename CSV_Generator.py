import streamlit as st
import pandas as pd
import random
import re

# ตั้งค่าหน้าเว็บ
st.set_page_config(layout="wide", page_title="Advanced Stock Photo Metadata Tool")

st.title("🚀 Advanced Stock Photo Metadata Generator")
st.markdown("เครื่องมือสร้างไฟล์ CSV สำหรับ Stock Photo พร้อมระบบสุ่ม Keywords และ Title อัจฉริยะ")

# --- ส่วนข้อมูลสำหรับ UI ---
ADOBE_CATEGORIES = [
    "1 - Animals", "2 - Architecture", "3 - Business", "4 - Drinks", "5 - Nature",
    "6 - Emotions", "7 - Food", "8 - Graphic", "9 - Hobbies", "10 - Industry",
    "11 - Landscape", "12 - Lifestyle", "13 - People", "14 - Plants", "15 - Culture",
    "16 - Science", "17 - Social Issues", "18 - Sports", "19 - Technology", 
    "20 - Transport", "21 - Travel"
]

CONNECTORS = ["with", "among", "between", "involving", "along", "featuring"]

# --- ฟังก์ชันช่วยเหลือ ---
def clean_keyword_list(text):
    """แปลง Text เป็น List ของคำ ตัดช่องว่างและคำว่างออก"""
    if not text:
        return []
    # แยกด้วยเครื่องหมายลูกน้ำ
    words = [w.strip() for w in text.split(',')]
    return [w for w in words if w]

def generate_shuffled_keywords(keywords, mode):
    """สลับตำแหน่ง Keywords ตามโหมด A, B, C"""
    if not keywords:
        return ""
    
    # แยกส่วน 7 คำแรก และส่วนที่เหลือ
    head = keywords[:7]
    tail = keywords[7:]
    
    # Mode A: สลับ 7 คำแรก, ส่วนหลังล็อค
    if mode == "A":
        random.shuffle(head)
        # tail เหมือนเดิม
        
    # Mode B: 7 คำแรกล็อค, สลับส่วนหลัง
    elif mode == "B":
        # head เหมือนเดิม
        random.shuffle(tail)
        
    # Mode C: สลับทั้ง 7 คำแรก และ สลับส่วนหลัง
    elif mode == "C":
        random.shuffle(head)
        random.shuffle(tail)
        
    # รวมกลับเป็น list เดียว
    final_list = head + tail
    return ", ".join(final_list)

def generate_smart_title(base_title, connector, all_keywords):
    """สร้าง Title ตามเงื่อนไข: Base + Connector + 5 Keywords (ไม่ซ้ำ, <200 chars)"""
    
    # 1. เตรียมคำห้ามซ้ำ (คำที่อยู่ใน Title หลัก)
    # แยกคำใน Title ออกมาเพื่อเช็ค (ใช้ set เพื่อความเร็วและ unique)
    forbidden_words = set(re.findall(r'\w+', base_title.lower()))
    
    # 2. กรอง Keywords ที่จะเอามาสุ่ม (ต้องไม่ซ้ำกับ Title)
    candidate_keywords = [
        kw for kw in all_keywords 
        if not (set(re.findall(r'\w+', kw.lower())) & forbidden_words)
    ]
    
    # ถ้าคำเหลือไม่พอ 5 คำ ก็ใช้เท่าที่มี
    num_to_pick = min(5, len(candidate_keywords))
    if num_to_pick == 0:
        return f"{base_title} {connector}" # ไม่มีคำเติม
        
    # 3. ลองสุ่มจนกว่าจะได้ความยาวไม่เกิน 200 (ลอง 10 ครั้งกันเหนียว)
    final_title_str = ""
    
    for _ in range(10): 
        picked = random.sample(candidate_keywords, num_to_pick)
        
        # จัดรูปแบบ: k1, k2, k3, k4 and k5
        if len(picked) > 1:
            suffix = ", ".join(picked[:-1]) + " and " + picked[-1]
        else:
            suffix = picked[0]
            
        temp_title = f"{base_title} {connector} {suffix}"
        
        # เช็คเงื่อนไข < 200 ตัวอักษร
        if len(temp_title) <= 200:
            final_title_str = temp_title
            break
    
    # ถ้าวนลูปแล้วยังเกิน 200 ให้ตัดเหลือแค่ Base (หรือลดจำนวนคำลง - ในที่นี้เอา Base ก่อนเพื่อความชัวร์)
    if not final_title_str:
         final_title_str = f"{base_title} {connector}"

    return final_title_str

# --- UI Layout ---

with st.form("metadata_form"):
    st.subheader("1. ตั้งค่าข้อมูลพื้นฐาน")
    
    col1, col2 = st.columns(2)
    with col1:
        # 1. Adobe Category
        selected_category_full = st.selectbox("Adobe Category", ADOBE_CATEGORIES, index=2) # Default Business
        # ดึงเลขออกมา (เช่น "3 - Business" -> "3")
        category_id = selected_category_full.split(" - ")[0]
        
    with col2:
        # 3. Connector Word
        connector = st.selectbox("Connector Word", CONNECTORS, index=0) # Default with

    # 2. Title
    base_title = st.text_input("Title (ใส่ได้ไม่เกิน 100 ตัวอักษร)", max_chars=100, value="Quality assurance concept")

    # 4. SEO Tags
    st.subheader("2. จัดการ Keywords & SEO")
    raw_keywords = st.text_area("SEO Tags (คั่นด้วยคอมม่า , )", height=150, 
                                value="assurance, quality, proposal, standard, value, approval, service, review, guarantee, best, performance, client, businessman, procedure")
    
    # ตัวเลือกโหมดการสุ่ม
    st.write("เลือกรูปแบบการสุ่ม Keywords:")
    mode_option = st.radio(
        "Mode Selection",
        [
            "A: สลับ 7 คำแรก (ส่วนหลังล็อค)", 
            "B: ล็อค 7 คำแรก (สลับส่วนหลัง)", 
            "C: สลับ 7 คำแรก และ สลับส่วนหลัง"
        ]
    )
    
    # แปลง Choice เป็นตัวแปร mode ("A", "B", "C")
    mode_map = {"A": "A", "B": "B", "C": "C"}
    selected_mode = mode_option.split(":")[0]

    submitted = st.form_submit_button("🚀 Generate CSV (100 Rows)")

# --- Processing ---
if submitted:
    if not base_title:
        st.error("กรุณาใส่ Title ก่อนครับ")
    elif not raw_keywords:
        st.error("กรุณาใส่ Keywords ก่อนครับ")
    else:
        # เตรียมข้อมูล
        keyword_list = clean_keyword_list(raw_keywords)
        data_rows = []
        
        # สร้าง 100 แถว
        for i in range(1, 101):
            filename = f"custom-{i:02d}.jpg"
            
            # 1. สร้าง Keywords (Column C) ตาม Mode
            # ต้อง copy list มาใหม่ทุกรอบ เพื่อไม่ให้กระทบต้นฉบับเวลา shuffle
            current_keywords_list = keyword_list[:] 
            final_keywords_str = generate_shuffled_keywords(current_keywords_list, selected_mode)
            
            # 2. สร้าง Title (Column B)
            # สุ่ม 5 คำจาก Keywords ทั้งหมด (ต้นฉบับ)
            final_title_str = generate_smart_title(base_title, connector, keyword_list)
            
            # เก็บข้อมูล
            data_rows.append({
                "Filename": filename,
                "Title": final_title_str,
                "Keywords": final_keywords_str,
                "Category": category_id,
                "Releases": "no" # ค่า Default
            })
            
        # สร้าง DataFrame
        df = pd.DataFrame(data_rows)
        
        # แสดงผลลัพธ์
        st.success("✅ สร้างข้อมูลเสร็จสิ้น! ดูตัวอย่างด้านล่าง")
        
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"แสดง 10 แถวแรกจากทั้งหมด {len(df)} แถว")
        
        # ปุ่ม Download CSV
        # แปลงเป็น CSV String พร้อม Quoting
        csv = df.to_csv(index=False, quotechar='"', quoting=1)
        
        st.download_button(
            label="💾 Download CSV File",
            data=csv,
            file_name="generated_metadata_100.csv",
            mime="text/csv",
            type="primary"
        )