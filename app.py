import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
from streamlit_mic_recorder import mic_recorder

# 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# 유사도 계산 함수 (구두점/대소문자 무시)
def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_mode' not in st.session_state: st.session_state.input_mode = {}

st.title("🚀 최강 문장 학습 도구")
st.markdown("### 가리고, 듣고, 말하며 배우는 스마트 학습기")

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150, placeholder="여러 문장을 입력하면 자동으로 분리됩니다.")

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 마스터 컨트롤
    col_ctrl1, col_ctrl2 = st.columns(2)
    with col_ctrl1:
        if st.button("👁️ 영어 전체 보이기/숨기기"):
            curr = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_en[i] = not curr
            st.rerun()

    st.write("---")
    
    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.input_mode: st.session_state.input_mode[idx] = False

        r1, r2, r3, r4 = st.columns([0.5, 4, 4, 1.5])
        r1.write(f"**{idx + 1}**")

        # 1. 영어 문장 (학습 모드)
        with r2:
            if st.session_state.show_en[idx]:
                st.success(sentence)
            elif st.session_state.input_mode[idx]:
                user_input = st.text_input("정답 입력:", key=f"in_{idx}")
                
                # 음성 녹음 (간소화)
                st.caption("🎤 마이크 버튼을 누르고 말씀하세요")
                audio = mic_recorder(start_prompt="녹음 시작", stop_prompt="녹음 완료", key=f"mic_{idx}")
                
                if user_input:
                    score = get_similarity(user_input, sentence)
                    if score >= 0.9:
                        st.session_state.show_en[idx] = True
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"다시 시도! (일치율: {int(score*100)}%)")
            else:
                st.info("🙈 문장이 숨겨졌습니다.")

        # 2. 한국어 번역
        with r3:
            st.write(translator.translate(sentence))

        # 3. 제어 버튼
        with r4:
            c1, c2, c3 = st.columns(3)
            if c1.button("👁️", key=f"e_{idx}"):
                st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                st.rerun()
            if c2.button("✍️", key=f"w_{idx}"):
                st.session_state.input_mode[idx] = not st.session_state.input_mode[idx]
                st.rerun()
            if c3.button("▶️", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3', autoplay=True)
else:
    st.info("영어 지문을 입력하면 학습이 시작됩니다.")
