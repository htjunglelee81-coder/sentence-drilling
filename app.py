import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# 2. 디자인: 입력창 내부에 마이크 아이콘 배치 및 높이 고정
st.markdown("""
    <style>
    /* 입력창 내부 우측 끝에 마이크 아이콘 배치 */
    .stTextInput > div > div > input {
        padding-right: 50px !important;
    }
    .mic-container {
        position: relative;
        top: -45px; /* 입력창 높이에 맞춰 마이크 버튼을 위로 올림 */
        float: right;
        right: 10px;
        z-index: 999;
    }
    .error-msg { color: red; font-weight: bold; font-size: 14px; margin-top: -15px; margin-bottom: 10px; }
    /* 문장 칸의 높이를 일정하게 유지 */
    .sentence-box { min-height: 60px; display: flex; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

def get_similarity(a, b):
    if not a: return 0
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

if 'show_en' not in st.session_state: st.session_state.show_en = {}

st.title("🚀 Smart English Learning Table")

# 3. 지문 입력 영역
with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 상단 버튼들
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
            # 원문 칸 (가려지면 입력창으로 변신)
            c_inner_txt, c_inner_eye = st.columns([10, 1.5])
            
            with c_inner_txt:
                if st.session_state.show_en[idx]:
                    # 원문 표시
                    st.success(sentence)
                else:
                    # [핵심] 원문 자리에 바로 입력창 배치
                    u_in = st.text_input(
                        "정답 입력", 
                        key=f"field_{idx}", 
                        placeholder="영어를 입력하거나 마이크를 클릭하세요",
                        label_visibility="collapsed"
                    )
                    
                    # 입력창 우측 끝에 겹쳐질 마이크 버튼
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
                    
                    # 오답 시 안내
                    if u_in:
                        if get_similarity(u_in, sentence) >= 0.9:
                            st.session_state.show_en[idx] = True
                            st.balloons(); st.rerun()
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
