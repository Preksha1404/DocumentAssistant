import streamlit as st
from utils import api_post, api_get

# ---------------- SESSION STATE -----------------
if "token" not in st.session_state:
    st.session_state.token = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent_chat_history" not in st.session_state:
    st.session_state.agent_chat_history = []

if "active_document_id" not in st.session_state:
    st.session_state.active_document_id = None

# ---------------- SIDEBAR NAV -----------------
st.sidebar.title("📄 Document Assistant")

if st.session_state.token:
    st.sidebar.success("Logged in")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.chat_history = []
else:
    st.sidebar.warning("Not Logged In")

page = st.sidebar.radio(
    "Navigation",
    ["Login", "Register", "Upload Document", "RAG Chat", "AI Agent", "Billing"]
)

# ------------------- LOGIN PAGE ---------------------
if page == "Login":
    st.header("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = api_post("/auth/login", json={"email": email, "password": password})

        if not res:
            st.error("Login failed")
        else:
            # Backend returns expected dict
            if "access_token" in res:
                st.session_state.token = res["access_token"]
                st.success("Logged in successfully!")

            # Backend returns list → [user, access_token, refresh_token]
            elif isinstance(res, list) and len(res) == 3:
                user = res[0]
                access_token = res[1]
                refresh_token = res[2]

                st.session_state.token = access_token
                st.success("Logged in successfully!")

            else:
                st.error("Unexpected response from server")

# ------------------- REGISTER PAGE ------------------
elif page == "Register":
    st.header("📝 Register")

    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    password = st.text_input("Password", type="password")

    if st.button("Create Account"):
        res = api_post("/auth/register", json={
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": password
        })
        if res:
            st.success("Account created! You may login now.")

# ------------------- UPLOAD DOC PAGE ----------------
elif page == "Upload Document":
    st.header("📤 Upload Document")

    if not st.session_state.token:
        st.warning("Login required.")
        st.stop()

    file = st.file_uploader("Upload PDF / TXT / DOCX", type=["pdf", "txt", "docx"])

    if st.button("Upload"):
        if file is None:
            st.error("Please upload a document")
        else:
            files = {"file": (file.name, file.getvalue())}
            res = api_post("/documents/upload", files=files, token=st.session_state.token)
            if res:
                st.success("Uploaded successfully!")
                st.session_state.active_document_id = res.get("document_id")
                st.info(f"Active document ID set to {st.session_state.active_document_id}")

# ------------------- RAG CHAT PAGE ------------------
elif page == "RAG Chat":
    st.header("💬 Ask Questions (RAG)")

    if not st.session_state.token:
        st.warning("Login required.")
        st.stop()

    # Chat history
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["text"])

    question = st.chat_input("Ask something about your document...")

    if question:
        st.session_state.chat_history.append({"role": "user", "text": question})
        st.chat_message("user").write(question)

        res = api_post("/rag/ask", json={"question": question}, token=st.session_state.token)

        if res:
            answer = res.get("answer", "No answer returned")
            st.session_state.chat_history.append({"role": "assistant", "text": answer})
            st.chat_message("assistant").write(answer)

# ------------------- AGENT CHAT PAGE ----------------
elif page == "AI Agent":
    st.header("🤖 AI Agent")

    if not st.session_state.token:
        st.warning("Login required.")
        st.stop()

    # Render agent chat history
    for msg in st.session_state.agent_chat_history:
        st.chat_message(msg["role"]).write(msg["text"])

    # Chat input (prevents duplicate rendering)
    agent_question = st.chat_input("Ask your AI Agent")

    if agent_question:
        # Save + show user message
        st.session_state.agent_chat_history.append({
            "role": "user",
            "text": agent_question
        })
        st.chat_message("user").write(agent_question)

        # Call agent API
        res = api_post(
            "/agent/ask",
            json={
                "query": agent_question,
                "document_id": st.session_state.active_document_id
            },
            token=st.session_state.token
        )

        if res:
            answer = res.get("response", "No response")
            st.session_state.agent_chat_history.append({
                "role": "assistant",
                "text": answer
            })
            st.chat_message("assistant").write(answer)
            

# ------------------- BILLING PAGE -------------------
elif page == "Billing":
    st.header("💳 Subscription / Billing")

    if not st.session_state.token:
        st.warning("Login required.")
        st.stop()

    # Fetch user subscription info
    sub = api_get("/billing/me/subscription", token=st.session_state.token)

    if not sub:
        st.error("Failed to load subscription details")
        st.stop()

    status = sub.get("subscription_status")
    trial_end = sub.get("trial_end")
    period_end = sub.get("current_period_end")

    # Display status
    st.info(f"**Status:** {status}")

    # Convert trial_end to readable format
    if trial_end:
        st.write(f"**Trial Ends:** {trial_end}")

    if period_end:
        st.write(f"**Billing Period Ends:** {period_end}")

    st.markdown("---")

    status = sub.get("subscription_status")

    if status == "trialing":
        st.info("🕒 You are on a free trial.")
    elif status == "active":
        st.success("✅ Subscription Active")
    elif status in ["past_due", "none"]:
        st.error("⛔ Trial expired. Please subscribe to continue.")

    st.subheader("Upgrade to Continue Usage")
    if status in ["trialing", "past_due"]:
        if st.button("Subscribe Now"):
            res = api_post("/billing/create-checkout-session", token=st.session_state.token)
            if res and "checkout_url" in res:
                st.markdown(f"[👉 Click Here to Pay]({res['checkout_url']})")

    st.markdown("---")
