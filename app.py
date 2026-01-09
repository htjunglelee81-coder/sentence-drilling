import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# 2. 디자인 설정: 입력창 내부에 마이크 아이콘 배치
st.markdown("""
    <style>
    .input-container {
        position: relative;
        width: 100%;
        margin-bottom: 10px;
    }
    .custom-input {
        width: 100%;
        padding: 10px 40px 10px 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 16px;
    }
    .mic-icon {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        cursor: pointer;
        background: none;
        border: none;
        font-size: 20px;
    }
    .error-msg { color: red; font-weight: bold; background-color: #fff5f5; padding: 10px; border: 1px solid red; border-radius: 5px; margin-top: 5px; }
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
    
    # 상단 전체 제어 버튼
    col_t1, col_t2, _ = st.columns([2, 2, 6])
    with col_t1:
        if st.button("👁️ 전체 보이기/숨기기"):
            all_s = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_en[i] = not all_s
            st.rerun()
    with col_t2:
        if st.button("🔊 전체 듣기"):
            tts = gTTS(text=" ".join(sentences), lang='en')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
    
    st.write("---")

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
                    
                    # [핵심] 입력창과 마이크 아이콘 통합 UI (HTML/JS)
                    # 별도의 Streamlit 위젯 대신 직접 HTML로 입력창을 렌더링하여 타이핑과 마이크 기능을 하나로 합침
                    u_in = st.text_input("정답 입력 (엔터):", key=f"input_{idx}", placeholder="영어를 입력하거나 오른쪽 마이크를 누르세요")
                    
                    # 마이크 버튼만 따로 작게 배치하여 입력창 바로 옆/끝에 위치시킴
                    if st.button(f"🎤", key=f"mic_btn_{idx}", help="클릭하고 영어로 말씀하세요"):
                        components.html(f"""
                            <script>
                            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                            recognition.lang = 'en-US';
                            recognition.start();
                            recognition.onresult = function(event) {{
                                var text = event.results[0][0].transcript;
                                // Streamlit의 입력창(input)을 찾아 값을 넣음
                                var inputs = window.parent.document.querySelectorAll('input');
                                for(var i=0; i<inputs.length; i++) {{
                                    if(inputs[i].getAttribute('aria-label') === null && inputs[i].type === 'text') {{
                                         // 현재 순서에 맞는 입력을 찾기 위해 key 매칭 (Streamlit 내부 구조 활용)
                                         if(inputs[i].id.includes('input_{idx}')) {{
                                             inputs[i].value = text;
                                             inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                             break;
                                         }}
                                    }}
                                }}
                            }};
                            </script>
                        """, height=0)
                    
                    if u_in:
                        if get_similarity(u_in, sentence) >= 0.9:
                            st.session_state.show_en[idx] = True
                            st.balloons(); st.rerun()
                        else:
                            st.markdown(f"<div class='error-msg'>❌ {u_in} (불일치)</div>", unsafe_allow_html=True)

            with c_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.rerun()

        with col_ko: st.write(translator.translate(sentence))
        with col_play:
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
