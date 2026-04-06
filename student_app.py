import streamlit as st
import requests
import streamlit.components.v1 as components
import io
import time
from PIL import Image
import plotly.graph_objects as go  # Радар диаграммасын сызуға арналған кітапхана

# ==========================================
# 1. ҚҰПИЯ ПАРАМЕТРЛЕР ЖӘНЕ БАПТАУЛАР
# ==========================================
SUPABASE_URL = "https://eytvntwumnptjddlsarg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5dHZudHd1bW5wdGpkZGxzYXJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk4ODgzNzgsImV4cCI6MjA4NTQ2NDM3OH0.zBn48hYdDVvuzE3ZBg86L8_-XNl7ikCGA4lK7yUJW20"  
TABLE_NAME = "submissions"

st.set_page_config(page_title="8-СЫНЫП: ФИЗИКА", layout="wide", page_icon="🧲")

def send_data(payload):
    """Supabase-ке дерек жіберу функциясы"""
    headers = {
        "apikey": SUPABASE_KEY, 
        "Authorization": f"Bearer {SUPABASE_KEY}", 
        "Content-Type": "application/json"
    }
    return requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", json=payload, headers=headers)

# ==========================================
# 2. ИНТЕРФЕЙС ЖӘНЕ СЕССИЯ ЖАДЫ
# ==========================================
def main():
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    if 'photos' not in st.session_state:
        st.session_state.photos = [] 
    if 'cam_key' not in st.session_state:
        st.session_state.cam_key = 0 

    st.markdown("""
        <style>
        body { -webkit-user-select: none; user-select: none; }
        input, textarea { -webkit-user-select: text !important; user-select: text !important; }
        .stApp { background-color: #f4f6f9; }
        .main-title { color: #1e3a8a; text-align: center; font-weight: 800; padding: 20px; border-bottom: 3px solid #3b82f6; }
        .search-section { background-color: #e0f2fe; padding: 25px; border-radius: 15px; border: 2px dashed #0284c7; margin-top: 50px; }
        .camera-box { background-color: #fef08a; padding: 20px; border-radius: 10px; border: 2px dashed #eab308; margin-bottom: 20px; }
        .chart-box { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-top: 15px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='main-title'>🧲 ФИЗИКА: 8-СЫНЫП (Тапсырма: Электромагниттік құбылыстар)</h1>", unsafe_allow_html=True)

    # ==========================================
    # 3. ТАПСЫРУ ПРОЦЕСІ
    # ==========================================
    if st.session_state.submitted:
        st.balloons()
        st.success("🎉 Жұмысың сәтті қабылданды! Төмендегі іздеу бөлімінен мұғалімнің (ЖИ) талдауын біле аласың.")
        if st.button("Қайта бастау 🔄"):
            st.session_state.submitted = False
            st.session_state.photos = []
            st.session_state.cam_key += 1
            st.rerun()
    else:
        st.info("📝 **Нұсқаулық:** Есепті дәптерге шығарып, әр бетті жеке түсіріп немесе жүктеп, «Тізімге қосу» батырмасын басыңыз. Соңында «Тапсыру» батырмасын басыңыз.")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("👤 Аты-жөніңіз (Мысалы: Асқаров Нұрлан):")
        with col2:
            s_class = st.selectbox("🏫 Сыныбыңыз:", ["8-A", "8-B", "8-C", "8-D"])

        if name:
            components.html(f"""
                <script>
                document.addEventListener('contextmenu', event => event.preventDefault());
                document.addEventListener('keydown', function(e) {{
                    if (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'p' || e.key === 'u' || e.key === 's')) {{
                        e.preventDefault();
                    }}
                }});

                let cheatCount = sessionStorage.getItem('cheatCount_{name}') || 0;
                cheatCount = parseInt(cheatCount);
                let isSubmitting = false;

                document.addEventListener("visibilitychange", function() {{
                    if (document.hidden && !isSubmitting) {{
                        cheatCount++;
                        sessionStorage.setItem('cheatCount_{name}', cheatCount);

                        if (cheatCount < 3) {{
                            alert("⚠️ АКАДЕМИЯЛЫҚ ФОКУС (" + cheatCount + "/3):\\n\\nНазарыңды тақырыпқа бұр, біз саған сенеміз! Басқа терезеге өтуге болмайды.");
                        }} else {{
                            alert("🚫 ЕРЕЖЕ ӨРЕСКЕЛ БҰЗЫЛДЫ:\\n\\nСіз 3 рет басқа терезеге өттіңіз. Жұмысыңыз нөлденді.");
                            
                            const payload = {{
                                student_name: "{name}",
                                student_class: "{s_class}",
                                status: "cheated",
                                answers: {{ "subject": "physics" }},
                                ai_feedback: "🚫 ЖҰМЫС ЖОЙЫЛДЫ: Оқушы тапсырма барысында басқа терезеге 3 реттен артық өтті."
                            }};
                            
                            fetch('{SUPABASE_URL}/rest/v1/{TABLE_NAME}', {{
                                method: 'POST',
                                headers: {{ 'apikey': '{SUPABASE_KEY}', 'Authorization': 'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json' }},
                                body: JSON.stringify(payload)
                            }}).then(() => {{ 
                                isSubmitting = true;
                                sessionStorage.removeItem('cheatCount_{name}');
                                window.parent.location.reload(); 
                            }});
                        }}
                    }}
                }});
                </script>
            """, height=0)

            st.markdown("<div class='camera-box'><b>📸 Жұмысты суретке түсіру немесе жүктеу:</b></div>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["📂 Телефоннан жүктеу", "📸 Камерамен түсіру"])
            
            with tab1:
                uploaded_file = st.file_uploader("Анық суретті таңдаңыз", type=["jpg", "jpeg", "png"], key=f"upload_{st.session_state.cam_key}")
                if uploaded_file:
                    if st.button("➕ Осы файлды жұмысқа тіркеу", use_container_width=True, key="btn_upload"):
                        st.session_state.photos.append(uploaded_file.getvalue())
                        st.session_state.cam_key += 1
                        st.rerun()

            with tab2:
                cam_image = st.camera_input("Дәптер бетін түсіріңіз", key=f"camera_{st.session_state.cam_key}")
                if cam_image:
                    if st.button("➕ Камерадағы суретті тіркеу", use_container_width=True, key="btn_cam"):
                        st.session_state.photos.append(cam_image.getvalue())
                        st.session_state.cam_key += 1 
                        st.rerun() 

            if st.session_state.photos:
                st.write("---")
                st.markdown(f"**Сіздің жұмысыңыз ({len(st.session_state.photos)} бет):**")
                cols = st.columns(min(len(st.session_state.photos), 4))
                
                for i, photo_bytes in enumerate(st.session_state.photos):
                    with cols[i % 4]:
                        st.image(photo_bytes, caption=f"{i+1}-бет", use_container_width=True)
                        if st.button(f"🗑️ Өшіру", key=f"delete_{i}"):
                            st.session_state.photos.pop(i)
                            st.rerun()
                
                st.write("---")
                
                if st.button("ЖҰМЫСТЫ ТАПСЫРУ ✅", type="primary", use_container_width=True):
                    with st.spinner("Суреттер біріктіріліп, мұғалімге жіберілуде..."):
                        
                        images = [Image.open(io.BytesIO(img_bytes)).convert("RGB") for img_bytes in st.session_state.photos]
                        widths, heights = zip(*(i.size for i in images))
                        stitched_image = Image.new('RGB', (max(widths), sum(heights)))
                        y_offset = 0
                        for img in images:
                            stitched_image.paste(img, (0, y_offset))
                            y_offset += img.height

                        img_byte_arr = io.BytesIO()
                        stitched_image.thumbnail((1500, 1500 * len(images))) 
                        stitched_image.save(img_byte_arr, format='JPEG', quality=80, optimize=True)
                        compressed_bytes = img_byte_arr.getvalue()
                        
                        file_name = f"student_{int(time.time())}.jpg"
                        
                        storage_url = f"{SUPABASE_URL}/storage/v1/object/exam_images/{file_name}"
                        storage_headers = {
                            "apikey": SUPABASE_KEY,
                            "Authorization": f"Bearer {SUPABASE_KEY}",
                            "Content-Type": "image/jpeg"
                        }
                        upload_res = requests.post(storage_url, headers=storage_headers, data=compressed_bytes)

                        if upload_res.status_code in [200, 201]:
                            public_image_url = f"{SUPABASE_URL}/storage/v1/object/public/exam_images/{file_name}"
                            payload = {
                                "exam_id": 1, 
                                "student_name": name, 
                                "student_class": s_class,
                                "answers": {"subject": "physics", "image_url": public_image_url},
                                "status": "pending"
                            }
                            resp = send_data(payload)
                            
                            if resp.status_code in [200, 201, 204]:
                                st.session_state.submitted = True
                                st.rerun()
                            else:
                                st.error(f"⚠️ Базаға сақтау қатесі: {resp.text}")
                        else:
                            st.error(f"⚠️ Қоймаға жүктеу қатесі: {upload_res.text}")

    # ==========================================
    # 4. НӘТИЖЕНІ ЖӘНЕ "ЦИФРЛЫҚ ЕГІЗДІ" КӨРСЕТУ
    # ==========================================
    st.markdown("<div class='search-section'><h3>🔎 Нәтижеңді және Когнитивті бейнеңді тексер</h3></div>", unsafe_allow_html=True)
    search_query = st.text_input("", key="search_input", placeholder="Іздеу үшін есіміңізді жазыңыз...")

    if search_query:
        s_headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        res = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?student_name=ilike.*{search_query}*&select=*&order=id.desc", headers=s_headers)
        
        if res.status_code == 200:
            results = res.json()
            if len(results) > 0:
                for data in results:
                    with st.container():
                        st.markdown(f"#### 👤 {data['student_name']} ({data['student_class']})")
                        if data['status'] == 'cheated':
                            st.error("🚫 Жұмыс жойылды: Академиялық фокус ережесі бұзылды.")
                        elif data['status'] == 'pending':
                            st.warning("⏳ Мұғалім (AI) әлі тексеріп жатыр. Сәл күте тұрыңыз...")
                        else:
                            # 1. Жалпы баға және ЖИ пікірі
                            col_score, col_fb = st.columns([1, 2])
                            with col_score:
                                raw_score = data.get('score', 0)
                                percentage = int((raw_score / 12) * 100) # 12 балл бойынша
                                st.metric("Жалпы нәтиже", f"{percentage}%", delta=f"{raw_score}/12 балл")
                                st.progress(min(raw_score / 12, 1.0))
                            with col_fb:
                                st.info(f"📝 **AI-Тьютордың талдауы:**\n\n{data.get('ai_feedback', 'Талдау жоқ.')}")
                            
                            # 2. ОҚУШЫНЫҢ ЦИФРЛЫҚ ЕГІЗІ (RADAR CHART)
                            st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
                            st.markdown("#### 🧠 Сенің «Дағдылар Картаң» (Digital Twin)")
                            
                            # MVP үшін балға негізделген логикалық модель
                            base_skill = percentage
                            categories = ['Формулаларды білу', 'Теорияны түсіну', 'Математикалық есептеу', 'ХБЖ (СИ) айналдыру', 'Логикалық талдау']
                            
                            skills = [
                                min(base_skill + 10, 100), 
                                min(base_skill + 5, 100),  
                                max(base_skill - 15, 10),  
                                max(base_skill - 25, 10),  
                                max(base_skill - 5, 10)    
                            ]

                            fig = go.Figure()
                            fig.add_trace(go.Scatterpolar(
                                r=skills,
                                theta=categories,
                                fill='toself',
                                name='Дағдылар',
                                line_color='#3b82f6',
                                fillcolor='rgba(59, 130, 246, 0.4)'
                            ))

                            fig.update_layout(
                                polar=dict(
                                    radialaxis=dict(visible=True, range=[0, 100])
                                ),
                                showlegend=False,
                                margin=dict(t=30, b=30, l=30, r=30),
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        st.markdown("<hr>", unsafe_allow_html=True)
            else:
                st.info("Бұл есіммен нәтиже табылмады.")

if __name__ == "__main__":
    main()