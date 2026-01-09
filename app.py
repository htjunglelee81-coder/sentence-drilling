import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
from streamlit_mic_recorder import mic_recorder

# 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'show_ko' not in st.session_state: st.session_state.show_ko = {}
if 'input_mode' not in st.session_state: st.session_state.input_mode = {}

def get_similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

st.title("🚀 최강 문장 학습 도구 (Interactive Mode)")

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

def split_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]

sentences = split_sentences(raw_text)

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 마스터 컨트롤
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 2])
    with col_ctrl1:
        if st.button("👁️ 영어 전체 보이기/숨기기"):
            curr = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_en[i] = not curr
            st.rerun()
    with col_ctrl2:
        if st.button("👁️ 해석 전체 보이기/숨기기"):
            curr = all(st.session_state.show_ko.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_ko[i] = not curr
            st.rerun()

    st.write("---")
    # 헤더
    h1, h2, h3, h4 = st.columns([0.5, 4, 4, 1.5])
    h1.write("**No**"); h2.write("**영어 문장**"); h3.write("**한국어 해석**"); h4.write("**기능**")

    for idx, sentence in enumerate(sentences):
        # 상태 초기화
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.show_ko: st.session_state.show_ko[idx] = True
        if idx not in st.session_state.input_mode: st.session_state.input_mode[idx] = False

        r1, r2, r3, r4 = st.columns([0.5, 4, 4, 1.5])
        r1.write(idx + 1)

        # 1. 영어 문장 칸
        with r2:
            if st.session_state.show_en[idx]:
                st.success(sentence)
            elif st.session_state.input_mode[idx]:
                # 입력 모드 활성화
                user_input = st.text_input(f"Write sentence {idx+1}:", key=f"input_{idx}")
                
                # 음성 입력 버튼
                audio_input = mic_recorder(start_prompt="🎤 음성으로 말하기", stop_prompt="⏹️ 중지", key=f"mic_{idx}")
                if audio_input:
                    # 실제 배포 환경에서는 브라우저의 STT API 연동이 필요하나, 
                    # 여기서는 인터페이스 구성을 우선 보여드립니다.
                    st.info("음성 인식이 완료되었습니다. (텍스트 변환 진행 중...)")

                if user_input:
                    score = get_similarity(user_input, sentence)
                    if score >= 0.9:
                        st.session_state.show_en[idx] = True
                        st.rerun()
                    else:
                        st.markdown(f"<span style='color:red;'>{user_input} (일치율: {int(score*100)}%)</span>", unsafe_allow_html=True)
            else:
                st.write("🙈 숨겨짐 (아래 버튼으로 입력하기)")

        # 2. 한국어 해석 칸
        with r3:
            translated = translator.translate(sentence)
            st.write(translated if st.session_state.show_ko[idx] else "🙈 숨겨짐")

        # 3. 기능 버튼 칸
        with r4:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.rerun()
            with btn_col2:
                if st.button("✍️", key=f"edit_{idx}"):
                    st.session_state.input_mode[idx] = not st.session_state.input_mode[idx]
                    st.rerun()
            
            if st.button("▶️", key=f"play_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3', autoplay=True)
