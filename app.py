import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
import streamlit.components.v1 as components

st.set_page_config(page_title="영문 학습 도구", layout="wide")

def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_option' not in st.session_state: st.session_state.input_option = {}

st.title("🚀 Smart English Learning Table")

with st.expander("📖 전체 영문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    st.write("---")

    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.input_option: st.session_state.input_option[idx] = None

        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_txt, c_eye = st.columns([10, 1.5])
            with c_txt:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    st.info("🙈 문장이 숨겨졌습니다.")
                    i1, i2, _ = st.columns([1, 1, 6])
                    
                    # 🎤 고성능 영어 인식 스크립트 실행
                    if i1.button("🎤", key=f"mic_btn_{idx}"):
                        st.session_state.input_option[idx] = 'mic'
                        components.html(f"""
                            <script>
                            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                            recognition.lang = 'en-US';
                            recognition.start();
                            recognition.onresult = function(event) {{
                                var transcript = event.results[0][0].transcript;
                                // 부모 창의 모든 입력창 중 현재 인덱스에 맞는 창을 찾아 값 주입
                                var inputs = window.parent.document.querySelectorAll('input');
                                for (var i = 0; i < inputs.length; i++) {{
                                    if (inputs[i].id.includes('user_in_{idx}')) {{
                                        inputs[i].value = transcript;
                                        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        break;
                                    }}
                                }}
                            }};
                            </script>
                        """, height=0)

                    if i2.button("✍️", key=f"write_btn_{idx}"):
                        st.session_state.input_option[idx] = 'write'

                    if st.session_state.input_option[idx]:
                        u_in = st.text_input("정답 입력 (엔터):", key=f"user_in_{idx}", placeholder="말씀하시거나 입력하세요")
                        
                        if u_in:
                            score = get_similarity(u_in, sentence)
                            if score >= 0.9:
                                st.session_state.show_en[idx] = True
                                st.balloons(); st.rerun()
                            else:
                                st.error(f"❌ {u_in} (다시 시도하세요!)")

            with c_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.session_state.input_option[idx] = None
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️ 재생", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
