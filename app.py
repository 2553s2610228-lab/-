import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="Morning Alarm Bot", page_icon="⏰")
st.title("⏰ 기상 알람 챗봇")
st.caption("여러분의 활기찬 아침을 열어주는 AI 알람 메이트입니다.")

# 2. Streamlit Secrets에서 API 키 불러오기 및 클라이언트 초기화
try:
    # streamlit의 secrets 양식에 맞춰 키를 가져옵니다.
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except KeyError:
    st.error("스마트폰 앱 설정 오류: .streamlit/secrets.toml 또는 Streamlit Cloud 대시보드에 'GEMINI_API_KEY'를 설정해주세요.")
    st.stop()

# 3. 세션 상태(Session State)를 활용한 채팅 기록 유지
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "좋은 아침이에요! ☀️ 오늘 아침은 개운하게 일어나셨나요? 오늘 날씨나 일정, 혹은 아침을 깨우는 가벼운 대화를 나눠봐요!"
        }
    ]

# 4. 이전 채팅 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력 및 챗봇 추론
if user_input := st.chat_input("메시지를 입력하세요 (예: 아침에 일어나는 꿀팁 알려줘)"):
    # 사용자 메시지 화면에 표시 및 저장
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI 답변 생성 (오류 처리 포함)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 기상 알람 앱 컨셉에 맞는 시스템 지침(System Instruction) 정의
        system_instruction = (
            "당신은 사용자의 기상을 돕고 아침을 활기차게 열어주는 '기상 알람 앱'의 AI 비서입니다. "
            "친절하고, 다정하며, 에너지가 넘치는 어조로 말하세요. 아침 인사, 잠 깨는 법, 시간 관리, "
            "간단한 날씨 대화(예시 상황) 등에 특화된 답변을 제공하세요."
        )
        
        # 모델에 전달할 대화 이력 포맷 변환 (role을 user/model로 매핑)
        contents = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))

        try:
            with st.spinner("알람 봇이 생각 중입니다... ☕"):
                # gemini-2.5-flash-lite 모델 호출
                response = client.models.generate_content(
                    model='gemini-2.5-flash-lite',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    )
                )
            
            ai_response = response.text
            message_placeholder.markdown(ai_response)
            
            # AI 답변을 세션 상태에 저장
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except APIError as e:
            # Gemini API 관련 오류 처리
            error_msg = f"Gemini API 오류가 발생했습니다: {e.message}"
            message_placeholder.error(error_msg)
        except Exception as e:
            # 기타 일반 오류 처리
            error_msg = f"예상치 못한 오류가 발생했습니다: {str(e)}"
            message_placeholder.error(error_msg)
