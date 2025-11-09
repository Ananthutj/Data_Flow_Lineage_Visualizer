import streamlit as st
import base64

st.title("🔐 Secure Streamlit Portal")

# Simulated URL parameter: data=YWxpY2VAY29tcGFueS5jb206MTIzNGFiY2QtNTY3OA==
params = st.experimental_get_query_params()
data_encoded = params.get("data", [""])[0]

# Decode
decoded = base64.b64decode(data_encoded).decode("utf-8")
url_email, token = decoded.split(":")

# Ask user to enter email
user_email = st.text_input("Enter your email:")

if st.button("Submit"):
    if user_email.strip().lower() != url_email.strip().lower():
        st.error("❌ Email does not match.")
    else:
        st.success(f"✅ Access granted! Welcome {user_email}")
        st.write("This is your secure Streamlit portal content.")
        st.write(f"(Token for internal use: {token})")


