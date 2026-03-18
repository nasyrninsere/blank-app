import streamlit as st

# 1. 텍스트 요소 출력하기
st.title("🎈 Streamlit 기본기 알아보기")
st.subheader("1. 텍스트 출력하기")

st.write("Streamlit에서는 `st.write()` 하나면 텍스트, 숫자, 데이터 등 웬만한 건 다 화면에 띄울 수 있습니다!")
st.text("이것은 일반 텍스트(st.text)입니다.")
st.markdown("**마크다운** 문법도 `st.markdown()`을 통해 자유롭게 사용할 수 있어요. *기울임꼴*도 가능하죠.")

st.divider() # 화면에 가로줄을 그어주는 기능입니다.

# 2. 사용자 입력 받기
st.subheader("2. 사용자 입력 받기")
st.write("사용자로부터 글자나 숫자를 입력받는 것도 매우 간단합니다.")

# 텍스트 입력
user_name = st.text_input("이름을 입력해 주세요:", placeholder="홍길동")

# 숫자 입력
user_age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=120, value=20)

# 3. 버튼과 상호작용 (인터랙션)
st.subheader("3. 버튼과 상호작용")
st.write("버튼을 누르면 파이썬 코드가 다시 실행되면서 화면이 업데이트됩니다.")

# 버튼 클릭 시 실행될 로직
if st.button("인사말 생성하기"):
    if user_name:
        st.success(f"안녕하세요, {user_name}님! {user_age}살이시군요. 반갑습니다! 👋")
        st.balloons() # 축하 효과 (풍선 애니메이션)
    else:
        st.warning("이름을 먼저 입력해 주세요!")
