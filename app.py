import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher

# 1. 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# 2. 스타일 설정 (오답 빨간 글씨)
st.markdown("""
    <style>
    .error-msg { color: red; font-weight: bold; padding: 5px; border-radius: 5px; background-color: #ffe6e6; }
    </style>
    """, unsafe_allow_html=True)

# 3. 유사도 점수 계산
def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_option' not in st.session_state: st.session_state.input_option = {}

st.title("🚀 최강 문장 학습 도구")

# 지문 입력
with st.expander("📖 여기에 영어 지문을 입력하세요", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 전체 제어 버튼
    if st.button("👁️ 영어 전체 보이기/숨기기"):
        curr = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
        for i in range(len(sentences)): 
            st.session_state.show_en[i] = not curr
            if not st.session_state.show_en[i]: st.session_state.input_option[i] = None
        st.rerun()

    st.write("---")

    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.input_option: st.session_state.input_option[idx] = None

        col_no, col_main, col_ko, col_play = st.columns([0.5, 5, 3, 1.5])
        
        col_no.write(f"**{idx + 1}**")

        # 영어 문장 칸
        with col_main:
            c_txt, c_eye = st.columns([10, 1.5]) # 눈알 버튼을 오른쪽 끝으로 배치
            
            with c_txt:
                if st.session_state.show_en[idx]:
                    st.success(sentence)
                else:
                    st.info("🙈 문장이 숨겨졌습니다. 아래 아이콘을 눌러 입력하세요.")
                    # 마이크 / 쓰기 선택
                    i1, i2, _ = st.columns([1, 1, 6])
                    if i1.button("🎤", key=f"m_{idx}"):
                        st.session_state.input_option[idx] = 'mic'
                        st.rerun()
                    if i2.button("✍️", key=f"w_{idx}"):
                        st.session_state.input_option[idx] = 'write'
                        st.rerun()

                    # 입력 방식에 따른 화면 표시
                    if st.session_state.input_option[idx] == 'write':
                        u_in = st.text_input("정답 입력 (엔터):", key=f"t_{idx}")
                        if u_in:
                            if get_similarity(u_in, sentence) >= 0.9:
                                st.session_state.show_en[idx] = True
                                st.balloons(); st.rerun()
                            else:
                                st.markdown(f"<div class='error-msg'>{u_in} (불일치)</div>", unsafe_allow_html=True)
                    
                    elif st.session_state.input_option[idx] == 'mic':
                        st.warning("🎤 입력창을 누르고 키보드의 마이크 버튼을 눌러 말씀하세요!")
                        u_in = st.text_input("음성 인식 결과 대기 중...", key=f"v_{idx}")
                        if u_in:
                            if get_similarity(u_in, sentence) >= 0.9:
                                st.session_state.show_en[idx] = True
                                st.balloons(); st.rerun()
                            else:
                                st.markdown(f"<div class='error-msg'>{u_in} (불일치)</div>", unsafe_allow_html=True)

            with c_eye:
                if st.button("👁️", key=f"eye_{idx}"):
                    st.session_state.show_en[idx] = not st.session_state.show_en[idx]
                    st.session_state.input_option[idx] = None
                    st.rerun()

        # 해석 칸
        with col_ko:
            st.write(translator.translate(sentence))

        # 재생 칸
        with col_play:
            if st.button("▶️ 재생", key=f"p_{idx}"):
                tts = gTTS(text=sentence, lang='en')
                fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp, format='audio/mp3', autoplay=True)
