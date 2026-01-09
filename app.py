import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
import json
import os
from difflib import SequenceMatcher
import streamlit.components.v1 as components

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="최종 통합 학습 도구", layout="wide")

st.markdown("""
    <style>
    .stTextInput > div > div > input { padding-right: 50px !important; }
    .mic-container { position: relative; top: -45px; float: right; right: 10px; z-index: 999; }
    .error-msg { color: red; font-weight: bold; font-size: 14px; margin-top: -15px; margin-bottom: 10px; }
    .stats-text { font-size: 1rem; color: #31333F; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 관리 함수 (가장 안전한 방식)
DATA_FILE = "study_data.json"

def get_all_saved_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            return json.loads(content) if content else {}
    except:
        return {}

def save_current_lesson(title, text, rate):
    try:
        data = get_all_saved_data()
        data[title] = {"text": text, "rate": rate}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"저장 중 오류 발생: {e}")
        return False

def get_similarity(a, b):
    if not a: return 0
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# 3. 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'is_solved' not in st.session_state: st.session_state.is_solved = {}
if 'input_text' not in st.session_state: st.session_state.input_text = ""
if 'learning_mode' not in st.session_state: st.session_state.learning_mode = False

# 4. 사이드바 (불러오기)
st.sidebar.title("📁 복습 리스트")
all_saved = get_all_saved_data()
if all_saved:
    picked_title = st.sidebar.selectbox("저장된 지문 선택", ["선택하세요"] + list(all_saved.keys()))
    if picked_title != "선택하세요":
        if st.sidebar.button("불러오기"):
            st.session_state.input_text = all_saved[picked_title]["text"]
            st.session_state.show_en = {}
            st.session_state.is_solved = {}
            st.session_state.learning_mode = False
            st.rerun()
else:
    st.sidebar.info("저장된 지문이 없습니다.")

st.title("🚀 English Sentence Driller")

# 5. 지문 입력 및 저장 영역
with st.expander("📖 지문 입력 및 저장 관리", expanded=not bool(st.session_state.input_text)):
    raw_text = st.text_area("영어 지문을 입력하세요:", value=st.session_state.input_text, height=150)
    
    col_s1, col_s2 = st.columns([7, 3])
    with col_s1:
        new_title = st.text_input("지문 제목:", placeholder="예: 3월 모의고사 20번")
    with col_s2:
        if st.button("💾 이 지문 저장하기"):
            if new_title and raw_text:
                # 현재 맞힌 개수 기준으로 rate 계산
                temp_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]
                current_solved = sum(st.session_state.is_solved.values())
                current_rate = (current_solved / len(temp_sentences) * 100) if temp_sentences else 0
                
                if save_current_lesson(new_title, raw_text, current_rate):
                    st.success(f"'{new_title}' 저장 완료!")
                    st.rerun()
            else:
                st.warning("제목과 지문을 입력해주세요.")

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 데이터 초기화
    if not st.session_state.show_en:
        st.session_state.show_en = {i: True for i in range(len(sentences))}
        st.session_state.is_solved = {i: False for i in range(len(sentences))}

    # 6. 상단 완성률 및 제어판
    solved_cnt = sum(st.session_state.is_solved.values())
    pct = (solved_cnt / len(sentences) * 100)

    c_top1, c_top2 = st.columns([6, 4])
    with c_top1:
        if st.session_state.learning_mode:
            st.markdown(f'<div class="stats-text">{pct:.1f}% ({solved_cnt}/{len(sentences)} 문장 완료)</div>', unsafe_allow_html=True)
    
    with c_top2:
        if st.button("🔄 리셋"):
            st.session_state.show_en = {i: True for i in range(len(sentences))}
            st.session_state.is_solved = {i: False for i in range(len(sentences))}
            st.session_state.learning_mode = False
            st.rerun()

    c_btn1, c_btn2, _ = st.columns([2.5, 2.5, 5])
    with c_btn1:
        if st.button("👁️ 전체 보이기/숨기기"):
            currently_all_shown = all(st.session_state.show_en.values())
            if currently_all_shown: # 숨기기 시작
                st.session_state.show_en = {i: False for i in range(len(sentences))}
                st.session_state.is_solved = {i: False for i in range(len(sentences))}
                st.session_state.learning_mode = True
            else: # 보이기 전환
                st.session_state.show_en = {i: True for i in range(len(sentences))}
            st.rerun()
            
    with c_btn2:
        if st.button("🔊 전체 듣기"):
            tts = gTTS(text=" ".join(sentences), lang='en')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)

    st.write("---")

    # 7. 문장별 학습 리스트
    for idx, sentence in enumerate(sentences):
        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_txt, c_eye = st.columns([10, 1.5])
            with c_txt:
                if st.session_state.show_en.get(idx, True):
                    # 직접 맞힌 문장만 초록색 표시
                    if st.session_state.is_solved.get(idx, False):
                        st.success(sentence)
                    else:
                        st.info(sentence)
                else:
                    # 입력창 디자인
                    u_in = st.text_input("정답 입력", key=f"f_{idx}", placeholder="타이핑하거나 마이크 클릭", label_visibility="collapsed")
                    st.markdown('<div class="mic-container">', unsafe_allow_html=True)
                    if st.button("🎤", key=f"m_{idx}"):
                        components.html(f"""
                            <script>
                            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                            recognition.lang = 'en-US';
                            recognition.start();
                            recognition.onresult = function(event) {{
                                var text = event.results[0][0].transcript;
                                var input = window.parent.document.querySelector('input[id*="f_{idx}"]');
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
                            st.session_state.is_solved[idx] = True
                            st.balloons(); st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {u_in}</div>", unsafe_allow_html=True)

            with c_eye:
                if st.button("👁️", key=f"e_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en.get(idx, True)
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
