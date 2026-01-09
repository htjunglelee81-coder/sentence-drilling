import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
import json
import os
from difflib import SequenceMatcher
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

st.markdown("""
    <style>
    .stTextInput > div > div > input { padding-right: 50px !important; }
    .mic-container { position: relative; top: -45px; float: right; right: 10px; z-index: 999; }
    .error-msg { color: red; font-weight: bold; font-size: 14px; margin-top: -15px; margin-bottom: 10px; }
    .stats-text { font-size: 1rem; color: #31333F; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

DATA_FILE = "saved_studies.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(title, content, rate):
    data = load_data()
    data[title] = {"content": content, "rate": rate}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_similarity(a, b):
    if not a: return 0
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# --- 세션 상태 초기화 ---
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'is_solved' not in st.session_state: st.session_state.is_solved = {} # 정답을 직접 맞힌 문장 추적
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'active_learning' not in st.session_state: st.session_state.active_learning = False # 숨기기 모드 활성화 여부

# --- 사이드바: 불러오기 ---
st.sidebar.title("📁 복습하기")
saved_lessons = load_data()
if saved_lessons:
    selected_title = st.sidebar.selectbox("저장된 지문 선택:", ["선택하세요"] + list(saved_lessons.keys()))
    if selected_title != "선택하세요":
        if st.sidebar.button("지문 불러오기"):
            st.session_state.input_text = saved_lessons[selected_title]["content"]
            st.session_state.show_en = {}
            st.session_state.is_solved = {}
            st.session_state.active_learning = False
            st.rerun()

st.title("🚀 English Sentence Driller")

# 1. 지문 입력 영역
with st.expander("📖 영어 지문 입력 및 관리", expanded=not bool(st.session_state.input_text)):
    raw_text = st.text_area("영어 지문을 입력하세요:", value=st.session_state.input_text, height=150)
    c_save1, c_save2 = st.columns([7, 3])
    with c_save1:
        save_title = st.text_input("저장 제목:", placeholder="제목 입력")
    with c_save2:
        if st.button("💾 저장하기"):
            if save_title and raw_text:
                total = len(re.split(r'(?<=[.!?])\s+', raw_text.strip()))
                solved = sum(st.session_state.is_solved.values())
                rate = (solved / total * 100) if total > 0 else 0
                save_data(save_title, raw_text, rate)
                st.success("저장 완료!")

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 초기 로드 시 전체 보이기 상태
    if not st.session_state.show_en:
        st.session_state.show_en = {i: True for i in range(len(sentences))}
        st.session_state.is_solved = {i: False for i in range(len(sentences))}

    # 2. 상단 완성률 및 리셋
    solved_count = sum(st.session_state.is_solved.values())
    completion_rate = (solved_count / len(sentences) * 100) if sentences else 0

    col_st1, col_st2 = st.columns([6, 4])
    with col_st1:
        # 학습 모드(전체 숨기기 이후)일 때만 완성률 표시
        if st.session_state.active_learning:
            st.markdown(f'<div class="stats-text">{completion_rate:.1f}% ({solved_count}/{len(sentences)} 문장 완료)</div>', unsafe_allow_html=True)
    
    with col_st2:
        if st.button("🔄 리셋"):
            st.session_state.show_en = {i: True for i in range(len(sentences))}
            st.session_state.is_solved = {i: False for i in range(len(sentences))}
            st.session_state.active_learning = False
            st.rerun()

    col_btn1, col_btn2, _ = st.columns([2.5, 2.5, 5])
    with col_btn1:
        if st.button("👁️ 전체 보이기/숨기기"):
            is_all_shown = all(st.session_state.show_en.values())
            if is_all_shown: # 숨기기 모드로 전환
                st.session_state.show_en = {i: False for i in range(len(sentences))}
                st.session_state.is_solved = {i: False for i in range(len(sentences))} # 완성률 초기화
                st.session_state.active_learning = True
            else: # 보이기 모드로 전환
                st.session_state.show_en = {i: True for i in range(len(sentences))}
                # 전체 보이기를 한다고 해서 모두 푼 것으로 처리하지 않음 (선생님 요청 반영)
            st.rerun()
            
    with col_btn2:
        if st.button("🔊 전체 듣기"):
            tts = gTTS(text=" ".join(sentences), lang='en')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)

    st.write("---")

    # 3. 문장별 학습 영역
    for idx, sentence in enumerate(sentences):
        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_inner_txt, c_inner_eye = st.columns([10, 1.5])
            with c_inner_txt:
                if st.session_state.show_en.get(idx, True):
                    # 정답을 맞힌 문장은 초록색 박스로 유지
                    if st.session_state.is_solved.get(idx, False):
                        st.success(sentence)
                    else:
                        st.info(sentence)
                else:
                    u_in = st.text_input("정답 입력", key=f"field_{idx}", placeholder="영어를 입력하거나 마이크 클릭", label_visibility="collapsed")
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
                            st.session_state.is_solved[idx] = True # 직접 맞힌 것만 기록!
                            st.balloons()
                            st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {u_in}</div>", unsafe_allow_html=True)

            with c_inner_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en.get(idx, True)
                    # 눈알 버튼을 눌러도 is_solved는 변하지 않음 (완성률 산정 제외)
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
