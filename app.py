import streamlit as st
from deep_translator import GoogleTranslator  # 에러 방지를 위해 라이브러리 교체
from gtts import gTTS
import io
import re

# 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'show_ko' not in st.session_state: st.session_state.show_ko = {}

st.title("🎧 Smart English Learning Table")
st.subheader("최신 파이썬 버전 대응 완료 (Sentence Drilling)")

# 1. 입력 영역
with st.expander("📖 여기에 전체 영문을 입력하세요", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하거나 복사해서 붙여넣으세요:", height=200)

def split_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]

sentences = split_sentences(raw_text)

if sentences:
    # 번역기 초기화 (최신 방식)
    translator = GoogleTranslator(source='en', target='ko')
    
    st.divider()
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 2])
    
    with col_ctrl1:
        if st.button("👁️ 영어 전체 보이기/숨기기"):
            current_state = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_en[i] = not current_state
            st.rerun()

    with col_ctrl2:
        if st.button("👁️ 해석 전체 보이기/숨기기"):
            current_state = all(st.session_state.show_ko.get(i, True) for i in range(len(sentences)))
            for i in range(len(sentences)): st.session_state.show_ko[i] = not current_state
            st.rerun()
    
    with col_ctrl3:
        if st.button("🔊 전체 지문 이어서 듣기"):
            full_audio_text = " ".join(sentences)
            tts_full = gTTS(text=full_audio_text, lang='en')
            fp_full = io.BytesIO()
            tts_full.write_to_fp(fp_full)
            st.audio(fp_full, format='audio/mp3', autoplay=True)

    st.write("")
    h1, h2, h3, h4 = st.columns([0.5, 4, 4, 2])
    h1.write("**번호**")
    h2.write("**영어 문장**")
    h3.write("**한국어 해석**")
    h4.write("**발음**")
    st.divider()

    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.show_ko: st.session_state.show_ko[idx] = True

        r1, r2, r3, r4 = st.columns([0.5, 4, 4, 2])
        r1.write(f"{idx + 1}")

        with r2:
            st.write(sentence if st.session_state.show_en[idx] else "🙈 (숨겨짐)")
            if st.button("👁️", key=f"btn_en_{idx}"):
                st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                st.rerun()

        with r3:
            # 수정된 번역 로직
            translated = translator.translate(sentence)
            st.write(translated if st.session_state.show_ko[idx] else "🙈 (숨겨짐)")
            if st.button("👁️", key=f"btn_ko_{idx}"):
                st.session_state.show_ko[idx] = not st.session_state.show_ko[idx]
                st.rerun()

        with r4:
            if st.button("▶️ 재생", key=f"play_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3', autoplay=True)
else:

    st.info("위 빈칸에 영어 지문을 입력하면 학습 테이블이 생성됩니다.")
