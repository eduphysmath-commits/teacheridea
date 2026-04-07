import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import time
from openai import OpenAI

# ==========================================
# 1. ҚҰПИЯ ПАРАМЕТРЛЕР ЖӘНЕ БАПТАУЛАР
# ==========================================
SUPABASE_URL = "https://eytvntwumnptjddlsarg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5dHZudHd1bW5wdGpkZGxzYXJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk4ODgzNzgsImV4cCI6MjA4NTQ2NDM3OH0.zBn48hYdDVvuzE3ZBg86L8_-XNl7ikCGA4lK7yUJW20"  

# Сіздің Groq кілтіңіз
GROQ_API_KEY = "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"

# Supabase Headers
headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# Groq баптаулары - OpenAI клиентін қолданып Groq серверіне қосылу
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1", # Groq сервері
)

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
st.title("📊 Мұғалім кабинеті: AI-Прогностика және Бағалау (Groq)")
st.write("Бұл парақшада оқушылардың жұмыстарын көріп, Groq ЖИ-көмекшісі арқылы талдау жасай аласыз.")
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
        
        MAX_SCORE = 25 
        
        # Пайызды есептеу
        percent = min(int((avg_score / MAX_SCORE) * 100), 100)
        
        col_stat, col_pred = st.columns([1, 2])
        
        with col_stat:
            st.metric("Сыныптың орташа балы", f"{percent}%", f"{round(avg_score, 1)}/{MAX_SCORE} балл")
            st.info(f"Барлығы: {len(submissions)} жұмыс тапсырылды")
            
        with col_pred:
            if st.button("🚨 Groq арқылы предиктивті болжам жасау", use_container_width=True):
                with st.spinner("Groq сыныптың қателерін талдап жатыр..."):
                    feedbacks = [sub.get('ai_feedback', '') for sub in submissions if sub.get('ai_feedback')]
                    
                    if len(feedbacks) > 0:
                        combined_text = "\n".join(feedbacks)
                        
                        # МАҢЫЗДЫ ӨЗГЕРІС: Қазақ тілінде токен көп кететіндіктен, 10,000 әріпке дейін ғана аламыз. Бұл 12,000 токендік лимитке нақты сыяды.
                        combined_text = combined_text[:10000]
                        
                        prompt = f"""
                        Сен мектептің бас дата-аналитигісің. Төменде физика пәнінен бір сынып оқушыларының жіберген қателері жинақталған:
                        {combined_text}
                        
                        Осы мәліметтерге сүйеніп, мұғалімге мынадай құрылымда қысқаша прогностикалық ескерту жаса:
                        1. 🔴 Ең осал тұс: Сыныптың басым бөлігі қандай ортақ қате жіберді?
                        2. 🔮 Предиктивті болжам: Келесі бақылауда оқушылар қандай тақырыптан сүрінуі ықтимал?
                        3. 💡 Мұғалімге ұсыныс: Келесі сабақтың жоспарын қалай өзгерту керек?
                        
                        Жауапты қазақ тілінде, нақты әрі кәсіби тілмен жаз.
                        """
                        try:
                            # Groq мәтіндік моделін қолдану
                            response = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            prediction = response.choices[0].message.content
                            st.warning(f"**AI-Прогностика (Ескерту):**\n\n{prediction}")
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
            if sub['status'] == 'cheated':
                status_emoji = "🚫"
            elif sub['status'] == 'done':
                status_emoji = "✅"
            else:
                status_emoji = "⏳"
                
            with st.expander(f"{status_emoji} {sub['student_name']} ({sub['student_class']}) - Қазіргі балл: {sub.get('score', 0)}"):
                
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
                
                # ЖИ-АССИСТЕНТ (GROQ VISION) БЛОГЫ
                st.markdown("<div class='ai-box'><b>🤖 AI-Тьютор (Groq): Жұмысты автоматты талдау</b></div>", unsafe_allow_html=True)
                
                if img_for_ai:
                    if st.button("🧠 Groq арқылы талдау (Сократтық диалог)", key=f"ai_btn_{sub['id']}"):
                        with st.spinner("Groq есептің логикалық қадамдарын оқып жатыр..."):
                            try:
                                # Суретті Base64 форматына айналдыру
                                buffered = BytesIO()
                                img_for_ai.convert("RGB").save(buffered, format="JPEG")
                                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                                
                                prompt = f"""
                                Сен физика пәнінің тәжірибелі мұғалімісің. Мына оқушының дәптерге шығарған есебін тексер.
                                1. Қатені тапсаң, дайын жауап берме! "Сократтық диалог" әдісімен бағыттаушы 1-2 сұрақ қой.
                                2. Оқушының қандай когнитивті қате (мысалы, формуланы шатастырды, СИ жүйесіне айналдырмады) жібергенін қысқаша көрсет.
                                3. Жауабыңды қазақ тілінде, жылы әрі мотивация беретіндей етіп жаз.
                                4. Егер жұмыс мінсіз болса, оқушыны мақтап, {MAX_SCORE} балл бер.
                                5. Жауаптың соңында 'Ұсынылатын балл: X/{MAX_SCORE}' деп нақты балл көрсет.
                                """
                                
                                # Groq Vision моделін қолдану
                                response = client.chat.completions.create(
                                    model="llama-3.2-11b-vision-preview",
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": [
                                                {"type": "text", "text": prompt},
                                                {
                                                    "type": "image_url",
                                                    "image_url": {
                                                        "url": f"data:image/jpeg;base64,{img_base64}"
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                )
                                
                                ai_response_text = response.choices[0].message.content
                                st.session_state[f"ai_text_{sub['id']}"] = ai_response_text
                                st.success("Groq талдауы сәтті аяқталды!")
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