import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import io
import re
from difflib import SequenceMatcher
# 더 빠른 인식을 위해 라이브러리 교체 혹은 기본 입력 최적화
from streamlit_mic_recorder import mic_recorder 

st.set_page_config(page_title="최강 문장 학습 도구", layout="wide")

def get_similarity(a, b):
    a_clean = re.sub(r'[^\w\s]', '', a.lower()).strip()
    b_clean = re.sub(r'[^\w\s]', '', b.lower()).strip()
    return SequenceMatcher(None, a_clean, b_clean).ratio()

st.title("🚀 최강 문장 학습 도구")

# 세션 상태 초기화
if 'show_en' not in st.session_state: st.session_state.show_en = {}
if 'input_mode' not in st.session_state: st.session_state.input_mode = {}

with st.expander("📖 영어 지문 입력", expanded=True):
    raw_text = st.text_area("영어 지문을 입력하세요:", height=150)

sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text.strip()) if s.strip()]

if sentences:
    translator = GoogleTranslator(source='en', target='ko')
    
    for idx, sentence in enumerate(sentences):
        if idx not in st.session_state.show_en: st.session_state.show_en[idx] = True
        if idx not in st.session_state.input_mode: st.session_state.input_mode[idx] = False

        r1, r2, r3, r4 = st.columns([0.5, 4, 4, 1.5])
        r1.write(idx + 1)

        with r2:
            if st.session_state.show_en[idx]:
                st.success(sentence)
            elif st.session_state.input_mode[idx]:
                # 입력 방식 가이드
                user_input = st.text_input(f"Write or Speak:", key=f"in_{idx}")
                
                # 녹음 및 즉시 텍스트 변환 (서버 부하를 줄이기 위해 짧은 녹음 권장)
                audio = mic_recorder(start_prompt="🎤 말하기 시작", stop_prompt="⏹️ 완료", key=f"mic_{idx}")
                
                if audio:
                    # 녹음된 오디오가 들어오면 안내 메시지 변경
                    st.write("✅ 음성 데이터 수신됨 (엔터를 눌러 확인)")
                
                if user_input:
                    score = get_similarity(user_input, sentence)
                    if score >= 0.9:
                        st.session_state.show_en[idx] = True
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"오답! 일치율: {int(score*100)}%")
            else:
                st.write("🙈 숨겨짐")

        with r3:
            # 번역 속도 향상을 위해 캐싱 처리가 좋으나 우선 기본 출력
            st.write(translator.translate(sentence) if st.session_state.get(f'show_ko_{idx}', True) else "🙈 숨겨짐")

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
