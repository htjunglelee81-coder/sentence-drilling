import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
import streamlit.components.v1 as components

st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# CSS: 디자인 유지 및 오답 스타일
st.markdown("""
    <style>
    .error-msg { color: red; font-weight: bold; background-color: #fff5f5; padding: 10px; border: 1px solid red; border-radius: 5px; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

if 'show_en' not in st.session_state: st.session_state.show_en = {}

st.title("🚀 Smart English Learning Table")

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True

        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_txt, c_eye = st.columns([10, 1.5])
            with c_txt:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    st.info("🙈 문장이 숨겨졌습니다.")
                    
                    # 🎤 마이크 버튼과 입력창
                    m_col, i_col = st.columns([1, 9])
                    with m_col:
                        # 마이크 클릭 시 브라우저 내장 인식 기능 실행
                        if st.button("🎤", key=f"mic_{idx}"):
                            components.html(f"""
                                <script>
                                var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                                recognition.lang = 'en-US';
                                recognition.start();
                                recognition.onresult = function(event) {{
                                    var text = event.results[0][0].transcript;
                                    var input = window.parent.document.querySelectorAll('input')[{idx}];
                                    input.value = text;
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                }};
                                </script>
                            """, height=0)
                    
                    with i_col:
                        u_in = st.text_input("정답 입력:", key=f"in_{idx}", label_visibility="collapsed", placeholder="말씀하시거나 입력하세요")
                    
                    if u_in:
                        if get_similarity(u_in, sentence) >= 0.9:
                            st.session_state.show_en[idx] = True
                            st.balloons(); st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {u_in} (일치하지 않음)</div>", unsafe_allow_html=True)

            with c_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
