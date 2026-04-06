import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import time
import google.generativeai as genai

# ==========================================
# 1. ҚҰПИЯ ПАРАМЕТРЛЕР ЖӘНЕ БАПТАУЛАР
# ==========================================
SUPABASE_URL = "https://eytvntwumnptjddlsarg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5dHZudHd1bW5wdGpkZGxzYXJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk4ODgzNzgsImV4cCI6MjA4NTQ2NDM3OH0.zBn48hYdDVvuzE3ZBg86L8_-XNl7ikCGA4lK7yUJW20"  
GEMINI_API_KEY = "AIzaSyA3yhaOVIcvD4Qw1ZtBOhVROEuW4oUqF-M"

# Supabase Headers
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# Gemini баптаулары (Егер қате шықса, 'gemini-1.5-flash-latest' деп өзгертіңіз)
genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-1.5-flash')

# Бет баптауы
st.set_page_config(page_title="Нәтижелер тақтасы | ten-edu", layout="wide", page_icon="📊")

# ==========================================
# 2. СТИЛЬ (CSS)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .student-card { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .ai-box { background-color: #eef2ff; padding: 15px; border-radius: 8px; border-left: 5px solid #4f46e5; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ДЕРЕКҚОРМЕН (SUPABASE) ЖҰМЫС ФУНКЦИЯЛАРЫ
# ==========================================
def get_exams():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/exams?order=id.desc&select=*", headers=headers)
    return res.json() if res.status_code == 200 else []

def get_submissions_by_exam(exam_id):
    res = requests.get(f"{SUPABASE_URL}/rest/v1/submissions?exam_id=eq.{exam_id}&order=created_at.desc&select=*", headers=headers)
    return res.json() if res.status_code == 200 else []

def update_submission_score(sub_id, new_score, teacher_feedback):
    payload = {"score": new_score, "ai_feedback": teacher_feedback, "status": "done"}
    res = requests.patch(f"{SUPABASE_URL}/rest/v1/submissions?id=eq.{sub_id}", json=payload, headers=headers)
    return res.status_code in [200, 204]

# ==========================================
# 4. НЕГІЗГІ ИНТЕРФЕЙС
# ==========================================
st.title("📊 Мұғалім кабинеті: AI-Прогностика және Бағалау")
st.write("Бұл парақшада оқушылардың жұмыстарын көріп, ЖИ-көмекші арқылы талдау жасай аласыз.")
st.write("---")

exams_list = get_exams()

if exams_list:
    exam_options = {exam['title']: exam['id'] for exam in exams_list}
    selected_exam_result = st.selectbox("Қай тапсырманың нәтижесін көргіңіз келеді?", list(exam_options.keys()))
    res_exam_id = exam_options[selected_exam_result]
    
    submissions = get_submissions_by_exam(res_exam_id)
    
    if submissions:
        # ==========================================
        # 5. ПРЕДИКТИВТІ АНАЛИТИКА (СЫНЫПТЫҢ БОЛЖАМЫ)
        # ==========================================
        st.markdown("### 🔮 Сыныптың Предиктивті Аналитикасы")
        
        # Сынып бойынша ортақ балды есептеу
        scores = [sub.get('score', 0) for sub in submissions if sub['status'] == 'done']
        avg_score = sum(scores) / len(scores) if len(scores) > 0 else 0
        
        col_stat, col_pred = st.columns([1, 2])
        
        with col_stat:
            st.metric("Сыныптың орташа балы", f"{int((avg_score/12)*100)}%", f"{round(avg_score, 1)}/12 балл")
            st.info(f"Барлығы: {len(submissions)} жұмыс тапсырылды")
            
        with col_pred:
            if st.button("🚨 ЖИ арқылы предиктивті болжам жасау", use_container_width=True):
                with st.spinner("ЖИ сыныптың когнитивті карталарын біріктіріп, талдап жатыр..."):
                    # Барлық оқушылардың қателерін бір мәтінге жинау
                    feedbacks = [sub.get('ai_feedback', '') for sub in submissions if sub.get('ai_feedback')]
                    
                    if len(feedbacks) > 0:
                        combined_text = "\n".join(feedbacks)
                        
                        prompt = f"""
                        Сен мектептің бас дата-аналитигісің. Төменде физика пәнінен бір сынып оқушыларының жіберген қателері жинақталған:
                        {combined_text}
                        
                        Осы мәліметтерге сүйеніп, мұғалімге мынадай құрылымда қысқаша прогностикалық ескерту жаса:
                        1. 🔴 Ең осал тұс: Сыныптың басым бөлігі қандай ортақ қате жіберді?
                        2. 🔮 Предиктивті болжам: Келесі бақылауда (БЖБ/ТЖБ) оқушылар қандай тақырыптан сүрінуі ықтимал?
                        3. 💡 Мұғалімге ұсыныс: Келесі сабақтың жоспарын қалай өзгерту керек?
                        
                        Жауапты қазақ тілінде, нақты әрі кәсіби тілмен жаз.
                        """
                        try:
                            # Gemini арқылы тексті талдау
                            prediction = vision_model.generate_content(prompt)
                            st.warning(f"**AI-Прогностика (Ескерту):**\n\n{prediction.text}")
                        except Exception as e:
                            st.error(f"Болжам жасау кезінде қате шықты: {e}")
                    else:
                        st.info("Болжам жасау үшін алдымен төмендегі оқушылардың жұмыстарын бағалаңыз (ЖИ талдауынан өткізіңіз).")
        
        st.write("---")
        st.markdown("### 📋 Оқушылардың жеке жұмыстары")

        # ==========================================
        # 6. ОҚУШЫЛАР ТІЗІМІ ЖӘНЕ ЖЕКЕ ТЕКСЕРУ
        # ==========================================
        for sub in submissions:
            # Статусқа байланысты эмоджи қою
            if sub['status'] == 'cheated':
                status_emoji = "🚫"
            elif sub['status'] == 'done':
                status_emoji = "✅"
            else:
                status_emoji = "⏳"
                
            with st.expander(f"{status_emoji} {sub['student_name']} ({sub['student_class']}) - Қазіргі балл: {sub.get('score', 0)}"):
                
                # Анти-чит ескертуі
                if sub['status'] == 'cheated':
                    st.error("🚫 БҰЛ ОҚУШЫ АНТИ-ЧИТ ЖҮЙЕСІНЕ ТҮСТІ! Емтихан кезінде басқа терезеге өтіп кеткен.")
                
                st.write("**📝 Оқушының жұмысы:**")
                answers_data = sub.get('answers', {})
                
                img_for_ai = None
                
                if isinstance(answers_data, dict):
                    # 1. URL сілтемесі бар сурет
                    if answers_data.get('image_url'):
                        st.image(answers_data['image_url'], width=500, caption="Оқушының дәптері")
                        try:
                            img_response = requests.get(answers_data['image_url'])
                            img_for_ai = Image.open(BytesIO(img_response.content))
                        except Exception as e:
                            st.error(f"Суретті жүктеу мүмкін болмады: {e}")
                            
                    # 2. Base64 суреттер
                    elif answers_data.get('images_base64', []):
                        images = answers_data['images_base64']
                        for img_b64 in images:
                            try:
                                img_decoded = Image.open(BytesIO(base64.b64decode(img_b64)))
                                st.image(img_decoded, width=500)
                                if not img_for_ai: 
                                    img_for_ai = img_decoded
                            except Exception:
                                st.error("Сурет форматы қате.")

                st.write("---")
                
                # ЖИ-АССИСТЕНТ (GEMINI) БЛОГЫ
                st.markdown("<div class='ai-box'><b>🤖 AI-Тьютор: Жұмысты автоматты талдау</b></div>", unsafe_allow_html=True)
                
                if img_for_ai:
                    if st.button("🧠 Gemini арқылы талдау (Сократтық диалог)", key=f"ai_btn_{sub['id']}"):
                        with st.spinner("ЖИ есептің логикалық қадамдарын оқып жатыр..."):
                            try:
                                prompt = """
                                Сен физика пәнінің тәжірибелі мұғалімісің. Мына оқушының дәптерге шығарған есебін тексер.
                                1. Қатені тапсаң, дайын жауап берме! "Сократтық диалог" әдісімен бағыттаушы 1-2 сұрақ қой.
                                2. Оқушының қандай когнитивті қате (мысалы, формуланы шатастырды, СИ жүйесіне айналдырмады) жібергенін қысқаша көрсет.
                                3. Жауабыңды қазақ тілінде, жылы әрі мотивация беретіндей етіп жаз.
                                4. Егер жұмыс мінсіз болса, оқушыны мақтап, 12 балл бер.
                                5. Жауаптың соңында 'Ұсынылатын балл: X/12' деп нақты балл көрсет.
                                """
                                ai_response = vision_model.generate_content([prompt, img_for_ai])
                                st.session_state[f"ai_text_{sub['id']}"] = ai_response.text
                                st.success("ЖИ талдауы сәтті аяқталды!")
                            except Exception as e:
                                st.error(f"ЖИ тексеру кезінде қате шықты: {e}")
                else:
                    st.warning("Бұл жұмыста тексеретін сурет жоқ.")

                st.write("---")
                
                # МҰҒАЛІМ АУДИТІ ЖӘНЕ БАҒАНЫ БЕКІТУ
                st.markdown("**✍️ Қорытынды бағалау және Бекіту**")
                
                default_feedback = st.session_state.get(f"ai_text_{sub['id']}", sub.get('ai_feedback', ''))

                col_score, col_btn = st.columns([3, 1])
                
                with col_score:
                    new_score = st.number_input("Қорытынды балл:", value=sub.get('score', 0), key=f"score_update_{sub['id']}")
                    new_feedback = st.text_area("Мұғалімнің пікірі (немесе ЖИ талдауы):", value=default_feedback, height=250, key=f"feedback_update_{sub['id']}")
                
                with col_btn:
                    st.write("") 
                    st.write("")
                    if st.button("Бағаны бекіту ✅", key=f"btn_update_{sub['id']}", use_container_width=True):
                        if update_submission_score(sub['id'], new_score, new_feedback):
                            st.success("Сақталды! Оқушы өз кабинетінен көре алады.")
                            time.sleep(1) 
                            st.rerun()
    else:
        st.info("Бұл тапсырма бойынша әзірге ешқандай оқушы жұмыс тапсырған жоқ.")
else:
    st.warning("⚠️ Базада ешқандай тапсырма табылған жоқ. Алдымен 'exams' кестесіне тақырыптарды қосыңыз.")