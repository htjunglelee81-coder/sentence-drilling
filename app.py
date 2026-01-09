import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
import json
import os
from difflib import SequenceMatcher
import streamlit.components.v1 as components

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="최강 문장 학습 시스템", layout="wide")

st.markdown("""
    <style>
    .stTextInput > div > div > input { padding-right: 50px !important; }
    .mic-container { position: relative; top: -45px; float: right; right: 10px; z-index: 999; }
    .error-msg { color: red; font-weight: bold; font-size: 14px; margin-top: -15px; margin-bottom: 10px; }
    .stats-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #ff4b4b; }
    .success-text { color: #09ab3b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 저장 경로 설정
DATA_FILE = "saved_studies.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(title, content, completion_rate):
    data = load_data()
    data[title] = {"content": content, "rate": completion_rate}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_similarity(a, b):
    if not a: return 0
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_text' not in st.session_state: st.session_state.input_text = ""

# --- 사이드바: 불러오기 기능 ---
st.sidebar.title("📁 복습하기 (불러오기)")
saved_lessons = load_data()
if saved_lessons:
    selected_title = st.sidebar.selectbox("저장된 지문 선택:", ["선택하세요"] + list(saved_lessons.keys()))
    if selected_title != "선택하세요":
        if st.sidebar.button("지문 불러오기"):
            st.session_state.input_text = saved_lessons[selected_title]["content"]
            st.session_state.show_en = {} # 불러올 때 상태 리셋
            st.rerun()
else:
    st.sidebar.info("저장된 지문이 없습니다.")

# --- 메인 화면 ---
st.title("🚀 Smart English Learning System")

# 1. 지문 입력 및 저장 영역
with st.expander("📖 영어 지문 입력 및 관리", expanded=not bool(st.session_state.input_text)):
    raw_text = st.text_area("영어 지문을 입력하세요:", value=st.session_state.input_text, height=150)
    
    c_save1, c_save2 = st.columns([7, 3])
    with c_save1:
        save_title = st.text_input("저장할 제목 입력:", placeholder="예: 중3 교과서 1과")
    with c_save2:
        if st.button("💾 현재 지문 저장하기"):
            if save_title and raw_text:
                # 저장 시 현재 완성률 계산 포함
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]
                done_count = sum(1 for i in range(len(sentences)) if st.session_state.show_en.get(i, False))
                rate = (done_count / len(sentences) * 100) if sentences else 0
                save_data(save_title, raw_text, rate)
                st.success(f"'{save_title}' 지문이 저장되었습니다! (완성률: {rate:.1f}%)")
            else:
                st.error("제목과 지문을 모두 입력해주세요.")

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 2. 완성률 및 상단 제어
    done_count = sum(1 for i in range(len(sentences)) if st.session_state.show_en.get(i, False))
    completion_rate = (done_count / len(sentences)) * 100

    col_st1, col_st2 = st.columns([6, 4])
    with col_st1:
        st.markdown(f"""
            <div class="stats-box">
                <h4>📊 학습 완성률: <b>{completion_rate:.1f}%</b> ({done_count}/{len(sentences)} 문장 완료)</h4>
            </div>
            """, unsafe_allow_html=True)
    
    with col_st2:
        st.write("") # 간격 맞춤
        if st.button("🔄 학습 상태 리셋 (완성률 0%)"):
            st.session_state.show_en = {i: False for i in range(len(sentences))}
            st.rerun()

    col_btn1, col_btn2, _ = st.columns([2, 2, 6])
    with col_btn1:
        if st.button("👁️ 전체 보이기/숨기기"):
            all_s = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_en[i] = not all_s
            st.rerun()
    with col_btn2:
        if st.button("🔊 전체 듣기"):
            tts = gTTS(text=" ".join(sentences), lang='en')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)

    st.write("---")

    # 3. 문장별 학습 영역
    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True

        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_inner_txt, c_inner_eye = st.columns([10, 1.5])
            with c_inner_txt:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    # 원문 자리에 입력창 배치
                    u_in = st.text_input("정답 입력", key=f"field_{idx}", placeholder="영어를 입력하거나 마이크를 클릭하세요", label_visibility="collapsed")
                    
                    st.markdown('<div class="mic-container">', unsafe_allow_html=True)
                    if st.button("🎤", key=f"mic_btn_{idx}"):
                        components.html(f"""
                            <script>
                            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                            recognition.lang = 'en-US';
                            recognition.start();
                            recognition.onresult = function(event) {{
                                var text = event.results[0][0].transcript;
                                var input = window.parent.document.querySelector('input[id*="field_{idx}"]');
                                if(input) {{
                                    input.value = text;
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                }}
                            }};
                            </script>
                        """, height=0)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if u_in:
                        if get_similarity(u_in, sentence) >= 0.9:
                            st.session_state.show_en[idx] = True
                            st.balloons()
                            st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {u_in}</div>", unsafe_allow_html=True)

            with c_inner_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
