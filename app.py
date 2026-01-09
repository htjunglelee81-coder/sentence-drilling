import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
import streamlit.components.v1 as components

# 1. 페이지 설정 및 디자인 (오답 시 빨간색 표시)
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")
st.markdown("""
    <style>
    .error-msg { color: red; font-weight: bold; background-color: #fff5f5; padding: 10px; border: 1px solid red; border-radius: 5px; margin-top: 5px; }
    .stButton > button { width: 100%; }
    /* 자동완성 방지 및 가독성 */
    input { autocomplete: off !important; font-size: 16px !important; }
    </style>
    """, unsafe_allow_html=True)

def get_similarity(a, b):
    if not a: return 0
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}

st.title("🚀 Smart English Learning Table")

# 2. 지문 입력 영역
with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # --- [상단 기능 버튼: 전체 숨기기 / 전체 듣기] ---
    col_top1, col_top2, _ = st.columns([2.5, 2.5, 5])
    with col_top1:
        if st.button("👁️ 영어 전체 보이기/숨기기"):
            all_shown = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_en[i] = not all_shown
            st.rerun()
    with col_top2:
        if st.button("🔊 영문 전체 듣기"):
            full_text = " ".join(sentences)
            tts = gTTS(text=full_text, lang='en')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
    
    st.write("---")

    # 3. 학습 영역 반복문
    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True

        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        col_no.write(f"**{idx + 1}**")

        with col_main:
            c_txt, c_eye = st.columns([10, 1.5]) # 눈알 버튼 우측 끝
            with c_txt:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    st.info("🙈 문장이 숨겨졌습니다.")
                    
                    # 마이크 버튼(좌)과 타이핑 입력창(우)을 확실히 분리
                    m_col, i_col = st.columns([1, 9])
                    with m_col:
                        if st.button("🎤", key=f"mic_{idx}"):
                            # 브라우저 음성 인식 실행 후 입력창에 텍스트 주입
                            components.html(f"""
                                <script>
                                var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                                recognition.lang = 'en-US';
                                recognition.start();
                                recognition.onresult = function(event) {{
                                    var text = event.results[0][0].transcript;
                                    var input = window.parent.document.querySelector('input[id*="in_field_{idx}"]');
                                    if(input) {{
                                        input.value = text;
                                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    }}
                                }};
                                </script>
                            """, height=0)
                    
                    with i_col:
                        # [타이핑 기능] 상시 노출되는 입력창
                        u_in = st.text_input(
                            "정답 입력", 
                            key=f"in_field_{idx}", 
                            placeholder="직접 입력하거나 마이크 버튼을 눌러주세요",
                            label_visibility="collapsed"
                        )
                    
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

        with col_ko:
            st.write(translator.translate(sentence))

        with col_play:
            if st.button("▶️ 재생", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
