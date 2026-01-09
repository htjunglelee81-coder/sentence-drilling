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
st.set_page_config(page_title="영문 학습 도구", layout="wide")

st.markdown("""
    <style>
    .stTextInput > div > div > input { padding-right: 50px !important; }
    .mic-container { position: relative; top: -45px; float: right; right: 10px; z-index: 999; }
    .error-msg { color: red; font-weight: bold; font-size: 14px; margin-top: -15px; margin-bottom: 10px; }
    .stats-text { font-size: 1rem; color: #31333F; margin-bottom: 10px; font-weight: normal; }
    </style>
    """, unsafe_allow_html=True)

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
if 'current_rate' not in st.session_state: st.session_state.current_rate = None # 초기값 None

# --- 사이드바: 불러오기 ---
st.sidebar.title("📁 복습하기")
saved_lessons = load_data()
if saved_lessons:
    selected_title = st.sidebar.selectbox("저장된 지문 선택:", ["선택하세요"] + list(saved_lessons.keys()))
    if selected_title != "선택하세요":
        if st.sidebar.button("지문 불러오기"):
            st.session_state.input_text = saved_lessons[selected_title]["content"]
            st.session_state.current_rate = saved_lessons[selected_title]["rate"]
            st.session_state.show_en = {} 
            st.rerun()

st.title("🚀 English Sentence Driller")

# 1. 지문 입력 및 저장
with st.expander("📖 영어 지문 입력 및 관리", expanded=not bool(st.session_state.input_text)):
    raw_text = st.text_area("영어 지문을 입력하세요:", value=st.session_state.input_text, height=150)
    
    c_save1, c_save2 = st.columns([7, 3])
    with c_save1:
        save_title = st.text_input("저장 제목:", placeholder="제목 입력")
    with c_save2:
        if st.button("💾 저장하기"):
            if save_title and raw_text:
                rate_to_save = st.session_state.current_rate if st.session_state.current_rate is not None else 0.0
                save_data(save_title, raw_text, rate_to_save)
                st.success("저장 완료!")
            else: st.error("입력 확인 요망")

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # [수정] 처음 입력 시 모든 문장을 보이게(True) 설정
    if not st.session_state.show_en:
        st.session_state.show_en = {i: True for i in range(len(sentences))}

    # 2. 상단 제어 및 완성률 표시
    done_count = sum(1 for i in range(len(sentences)) if st.session_state.show_en.get(i, False))
    
    col_st1, col_st2 = st.columns([6, 4])
    with col_st1:
        # [수정] 완성률 노출 제어: current_rate가 None이 아닐 때만 표시
        if st.session_state.current_rate is not None:
            st.markdown(f'<div class="stats-text">{st.session_state.current_rate:.1f}% ({done_count}/{len(sentences)} 문장 완료)</div>', unsafe_allow_html=True)
    
    with col_st2:
        if st.button("🔄 리셋"):
            st.session_state.show_en = {i: True for i in range(len(sentences))}
            st.session_state.current_rate = None # 리셋 시 완성률 숨김
            st.rerun()

    col_btn1, col_btn2, _ = st.columns([2.5, 2.5, 5])
    with col_btn1:
        if st.button("👁️ 전체 보이기/숨기기"):
            # 현재 모든 문장이 보여지고 있는지 확인
            is_currently_all_shown = all(st.session_state.show_en.values())
            new_status = not is_currently_all_shown
            
            for i in range(len(sentences)): 
                st.session_state.show_en[i] = new_status
            
            # [수정] 전체 숨기기를 하면 0%, 전체 보이기를 하면 100% 산정
            if new_status: # 전체 보이기 완료
                st.session_state.current_rate = 100.0
            else: # 전체 숨기기 시작
                st.session_state.current_rate = 0.0
            st.rerun()
            
    with col_btn2:
        if st.button("🔊 전체 듣기"):
            tts = gTTS(text=" ".join(sentences), lang='en')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)

    st.write("---")

    # 3. 문장별 학습
    for idx, sentence in enumerate(sentences):
        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_inner_txt, c_inner_eye = st.columns([10, 1.5])
            with c_inner_txt:
                if st.session_state.show_en.get(idx, True):
                    st.success(sentence)
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
                            st.balloons()
                            st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {u_in}</div>", unsafe_allow_html=True)

            with c_inner_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en.get(idx, True)
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
