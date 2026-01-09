import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
from streamlit_speech_recorder import speech_recorder

st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# CSS: 오답 표시 및 레이아웃
st.markdown("""
    <style>
    .error-msg { color: red; font-weight: bold; background-color: #fff5f5; padding: 8px; border-radius: 5px; border: 1px solid red; margin-top: 5px; }
    /* 녹음 버튼 커스텀 스타일링은 라이브러리 특성상 제한적이나 최대한 깔끔하게 배치 */
    </style>
    """, unsafe_allow_html=True)

def get_similarity(a, b):
    if not a: return 0
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_mode' not in st.session_state: st.session_state.input_mode = {}

st.title("🚀 Smart English Sentence Driller")

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.input_mode: st.session_state.input_mode[idx] = None

        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_txt, c_eye = st.columns([10, 1.5])
            with c_txt:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    st.info("🙈 문장이 숨겨졌습니다.")
                    i1, i2, _ = st.columns([1.5, 1, 6])
                    
                    with i1:
                        # 마이크 아이콘 클릭 시 즉시 녹음/변환 (영어 설정)
                        st.write("🎤")
                        recorded_text = speech_recorder(text="", key=f"speech_{idx}", language="en-US")
                    
                    with i2:
                        if st.button("✍️", key=f"w_btn_{idx}"):
                            st.session_state.input_mode[idx] = 'write'
                    
                    # 입력 처리 로직
                    final_input = ""
                    if recorded_text:
                        final_input = recorded_text
                    elif st.session_state.input_mode[idx] == 'write':
                        final_input = st.text_input("타이핑 후 엔터:", key=f"t_in_{idx}")

                    if final_input:
                        score = get_similarity(final_input, sentence)
                        if score >= 0.9:
                            st.session_state.show_en[idx] = True
                            st.balloons()
                            st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {final_input} (일치율: {int(score*100)}%)</div>", unsafe_allow_html=True)

            with c_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.session_state.input_mode[idx] = None
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
