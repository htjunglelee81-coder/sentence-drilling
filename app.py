import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
from streamlit_components_auth import st_auth # 대체 수단 혹은 자바스크립트 활용

# 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# 자바스크립트를 이용한 브라우저 음성 인식 구현 (속도 최상)
def stt_script(idx):
    return f"""
    <script>
    var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = function(event) {{
        var transcript = event.results[0][0].transcript;
        const input = window.parent.document.querySelectorAll('input')[{idx}];
        input.value = transcript;
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }};
    
    recognition.start();
    </script>
    """

def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_option' not in st.session_state: st.session_state.input_option = {}

st.title("🚀 최강 문장 학습 도구")

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    if st.button("👁️ 영어 전체 보이기/숨기기"):
        curr = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
        for i in range(len(sentences)): st.session_state.show_en[i] = not curr
        st.rerun()

    st.write("---")

    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.input_option: st.session_state.input_option[idx] = None

        r1, r2, r3, r4 = st.columns([0.5, 5, 3, 1.5])
        r1.write(f"**{idx + 1}**")

        with r2:
            inner_col1, inner_col2 = st.columns([11, 1])
            
            with inner_col1:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    st.info("🙈 문장이 숨겨졌습니다.")
                    
                    # 마이크 및 쓰기 선택 버튼 (나란히 배치)
                    opt_col1, opt_col2, _ = st.columns([0.5, 0.5, 5])
                    mic_clicked = opt_col1.button("🎤", key=f"m_btn_{idx}")
                    write_clicked = opt_col2.button("✍️", key=f"w_btn_{idx}")

                    if mic_clicked: st.session_state.input_option[idx] = 'mic'
                    if write_clicked: st.session_state.input_option[idx] = 'write'

                    # 입력창 제공
                    if st.session_state.input_option[idx]:
                        u_input = st.text_input("정답을 입력하세요 (엔터):", key=f"text_{idx}")
                        
                        if st.session_state.input_option[idx] == 'mic' and mic_clicked:
                            st.components.v1.html(stt_script(idx), height=0)
                            st.warning("🎤 지금 말씀하세요! (인식 후 입력창에 자동 입력됩니다)")

                        if u_input:
                            score = get_similarity(u_input, sentence)
                            if score >= 0.9:
                                st.session_state.show_en[idx] = True
                                st.balloons(); st.rerun()
                            else:
                                st.markdown(f"<p style='color:red; font-weight:bold;'>{u_input} (오답 - {int(score*100)}% 일치)</p>", unsafe_allow_html=True)

            with inner_col2: # 눈알 버튼을 원문 칸의 제일 오른쪽 끝에 배치
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.session_state.input_option[idx] = None
                    st.rerun()

        with r3: # 해석 칸
            st.write(translator.translate(sentence))

        with r4: # 재생 버튼
            if st.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
