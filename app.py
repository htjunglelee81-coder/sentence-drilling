import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
import time
from difflib import SequenceMatcher
import streamlit.components.v1 as components

st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# CSS: 오답 스타일 및 정답 유출 방지
st.markdown("""
    <style>
    .error-text { color: #D32F2F; font-weight: bold; padding: 10px; background-color: #FFEBEE; border: 1px solid #D32F2F; border-radius: 5px; margin-top: 5px; }
    /* 자동완성 목록 강제 숨기기 */
    input { -webkit-text-security: none; autocomplete: off !important; }
    </style>
    """, unsafe_allow_html=True)

def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_option' not in st.session_state: st.session_state.input_option = {}
# 자동완성 방지용 무작위 키 생성
if 'seed' not in st.session_state: st.session_state.seed = time.time()

st.title("🚀 최강 문장 학습 도구")

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
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
                    
                    if i1.button("🎤", key=f"m_btn_{idx}"):
                        st.session_state.input_option[idx] = 'mic'
                        # 영어 전용 고성능 STT 엔진 호출
                        components.html(f"""
                            <script>
                            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                            recognition.lang = 'en-US';
                            recognition.start();
                            recognition.onresult = function(event) {{
                                var text = event.results[0][0].transcript;
                                var inputs = window.parent.document.querySelectorAll('input');
                                for(var i=0; i<inputs.length; i++) {{
                                    if(inputs[i].id.indexOf('user_in_{idx}') !== -1) {{
                                        inputs[i].value = text;
                                        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        break;
                                    }}
                                }}
                            }};
                            </script>
                            """, height=0)

                    if i2.button("✍️", key=f"w_btn_{idx}"):
                        st.session_state.input_option[idx] = 'write'

                    if st.session_state.input_option[idx]:
                        # key에 seed를 섞어서 브라우저가 자동완성을 못하게 방해함
                        u_in = st.text_input(
                            "정답 입력:", 
                            key=f"user_in_{idx}_{st.session_state.seed}", 
                            label_visibility="collapsed",
                            placeholder="영어로 입력하거나 마이크를 클릭하세요",
                            autocomplete="new-password" 
                        )
                        
                        if u_in:
                            score = get_similarity(u_in, sentence)
                            if score >= 0.9:
                                st.session_state.show_en[idx] = True
                                st.balloons()
                                # 정답을 맞추면 시드를 갱신하여 다음 기록 삭제
                                st.session_state.seed = time.time()
                                st.rerun()
                            else:
                                st.markdown(f"<div class='error-text'>❌ {u_in} (다시 시도해 보세요!)</div>", unsafe_allow_html=True)

            with c_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.session_state.input_option[idx] = None
                    st.rerun()

        with col_ko:
            st.write(translator.translate(sentence))

        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
