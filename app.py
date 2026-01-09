import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
import streamlit.components.v1 as components

st.set_page_config(page_title="영문 학습 도구", layout="wide")

# CSS: 오답 스타일
st.markdown("<style>.error-msg { color: red; font-weight: bold; background-color: #fff5f5; padding: 10px; border: 1px solid red; border-radius: 5px; }</style>", unsafe_allow_html=True)

def get_similarity(a, b):
    if not a: return 0
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
    
    # 상단 버튼 (전체 제어)
    c1, c2, _ = st.columns([2, 2, 6])
    with c1:
        if st.button("👁️ 전체 보이기/숨기기"):
            all_s = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_en[i] = not all_s
            st.rerun()
    with c2:
        if st.button("🔊 전체 듣기"):
            tts = gTTS(text=" ".join(sentences), lang='en')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)

    st.write("---")

    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True

        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            # 원문 및 눈알 버튼
            c_txt, c_eye = st.columns([10, 1.5])
            with c_txt:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    # [복구된 타이핑 및 마이크 영역]
                    st.info("🙈 문장이 숨겨졌습니다.")
                    
                    # 1. 마이크 버튼
                    if st.button(f"🎤 음성으로 정답 말하기 (문장 {idx+1})", key=f"mic_{idx}"):
                        components.html(f"""
                            <script>
                            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                            recognition.lang = 'en-US';
                            recognition.start();
                            recognition.onresult = function(event) {{
                                var text = event.results[0][0].transcript;
                                var input = window.parent.document.querySelector('input[aria-label="answer_input_{idx}"]');
                                if(input) {{
                                    input.value = text;
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                }}
                            }};
                            </script>
                        """, height=0)
                    
                    # 2. 타이핑 입력창 (무조건 보이게 수정)
                    # label을 명시적으로 주고 aria_label을 활용해 자바스크립트가 찾기 쉽게 함
                    u_in = st.text_input(
                        "직접 타이핑하여 정답 입력 (엔터):", 
                        key=f"input_box_{idx}",
                        placeholder="여기에 영어를 입력하세요",
                        help="마이크를 쓰거나 직접 입력할 수 있습니다.",
                        label_visibility="visible" # 확실하게 보이도록 설정
                    )
                    
                    if u_in:
                        if get_similarity(u_in, sentence) >= 0.9:
                            st.session_state.show_en[idx] = True
                            st.balloons(); st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {u_in} (일치율 부족)</div>", unsafe_allow_html=True)

            with c_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
