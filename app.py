import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher

# 페이지 설정
st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

# CSS: 정답 노출 방지 및 UI 고정
st.markdown("""
    <style>
    .error-box { 
        color: #FF4B4B; 
        font-weight: bold; 
        background-color: #FFF5F5; 
        padding: 8px; 
        border-radius: 5px; 
        margin-top: 5px; 
        border: 1px solid #FF4B4B; 
        font-size: 0.9em;
    }
    /* 자동 완성 및 툴팁 방지 */
    div[data-baseweb="input"] input {
        text-overflow: clip !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_option' not in st.session_state: st.session_state.input_option = {}

st.title("🚀 최강 문장 학습 도구")

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("학습할 영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    # 전체 제어
    if st.button("👁️ 영어 전체 보이기/숨기기"):
        curr = all(st.session_state.show_en.get(i, True) for i in range(len(sentences)))
        for i in range(len(sentences)): 
            st.session_state.show_en[i] = not curr
            st.session_state.input_option[i] = None
        st.rerun()

    st.write("---")

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
                    
                    # 🎤 마이크 아이콘 클릭 시: 입력창만 열어주고 안내 문구 표시
                    if i1.button("🎤", key=f"m_btn_{idx}"):
                        st.session_state.input_option[idx] = 'mic'
                    # ✍️ 쓰기 아이콘 클릭 시: 일반 입력창 표시
                    if i2.button("✍️", key=f"w_btn_{idx}"):
                        st.session_state.input_option[idx] = 'write'

                    if st.session_state.input_option[idx]:
                        placeholder_text = "영어로 말씀하세요 (마이크 아이콘 클릭)" if st.session_state.input_option[idx] == 'mic' else "정답을 입력하세요"
                        
                        # 중요: label_visibility="collapsed"로 정답 툴팁 노출 방지
                        u_in = st.text_input(
                            f"input_{idx}", 
                            key=f"user_in_{idx}", 
                            placeholder=placeholder_text,
                            label_visibility="collapsed"
                        )
                        
                        if st.session_state.input_option[idx] == 'mic':
                            st.caption("💡 **Tip**: 입력창을 클릭한 뒤, **키보드의 마이크 버튼(Win+H 또는 스마트폰 마이크)**을 누르면 훨씬 정확하게 입력됩니다!")

                        if u_in:
                            score = get_similarity(u_in, sentence)
                            if score >= 0.9:
                                st.session_state.show_en[idx] = True
                                st.balloons(); st.rerun()
                            else:
                                st.markdown(f"<div class='error-box'>❌ {u_in} (불일치: {int(score*100)}%)</div>", unsafe_allow_html=True)

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
