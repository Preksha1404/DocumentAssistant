import streamlit as st
from utils import api_post, api_get, require_access_or_redirect
from datetime import datetime, timezone

redirect_page = st.query_params.get("page")

def clear_query_params():
    st.query_params.clear()

if redirect_page == "payment_success":
    st.success("🎉 Payment Successful!")
    st.markdown("### Your subscription is now active.")
    st.info("You can now access all premium features.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Go to Billing"):
            clear_query_params()
            st.rerun()

    with col2:
        if st.button("Go to Dashboard"):
            clear_query_params()
            st.rerun()

    st.stop()

if redirect_page == "payment_cancel":
    st.error("❌ Payment Cancelled")
    st.markdown("Your payment was not completed.")
    st.warning("You can retry the payment anytime from Billing.")

    if st.button("Back to Billing"):
        clear_query_params()
        st.rerun()

    st.stop()

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
st.sidebar.title("Document Assistant")

if st.session_state.token:
    st.sidebar.success("Logged in")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.chat_history = []
else:
    st.sidebar.warning("Not Logged In")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Login", "Register", "Upload Document", "RAG Chat", "AI Agent"]
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

# ------------------- HOME PAGE ---------------------
elif page == "Home":
    st.header("🏠 Welcome to Document Assistant AI")

    if not st.session_state.token:
        st.info("Please login to start using the platform.")
        st.markdown("""
        **What you get**
        - AI-powered document understanding
        - Multimodal RAG (PDFs, tables, images)
        - Intelligent AI Agent
        """)
        st.stop()

    sub = api_get("/billing/me/subscription", token=st.session_state.token)

    if not sub:
        st.error("Unable to load plan details.")
        st.stop()

    status = sub.get("subscription_status")
    trial_end = sub.get("trial_end")
    period_end = sub.get("current_period_end")

    now = datetime.now(timezone.utc)

    st.markdown("---")

    # ================= PLAN STATUS =================
    if status == "trialing" and trial_end:
        remaining = trial_end - now
        hours_left = max(int(remaining.total_seconds() // 3600), 0)

        st.success(
            f"""
            🧪 **1-Day Free Trial Active**  
            You can try all premium features.  
            ⏳ **{hours_left} hours remaining**
            """
        )

    elif status == "active":
        st.success(
            """
            ✅ **Subscription Active**  
            You have full access to all features.
            """
        )

    else:
        st.warning(
            """
            🔒 **Subscription Required**  

            To upload documents, chat with AI, and use the AI Agent,
            you need an active subscription.

            🎁 **Good news:** You get a **1-day free trial** when you upgrade.
            """
        )

    st.markdown("---")

    # ================= CTA =================
    if status in ["trialing", "active"]:
        st.button("✅ You Have Access", disabled=True)
    else:
        if st.button("🚀 Start Free Trial"):
            res = api_post(
                "/billing/create-checkout-session",
                token=st.session_state.token
            )
            if res and "checkout_url" in res:
                st.markdown(f"👉 [Proceed to Checkout]({res['checkout_url']})")

    st.markdown(
        """
        **What’s included**
        - Unlimited document uploads  
        - RAG-based question answering  
        - AI Agent reasoning  
        - Image & table understanding  
        """
    )

elif page == "Upload Document":
    st.header("📤 Upload Document")

    if not st.session_state.token:
        st.warning("Login required.")
        st.stop()

    allowed, _ = require_access_or_redirect()

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

# ------------------- RAG CHAT PAGE ------------------
elif page == "RAG Chat":
    st.header("💬 Ask Questions (RAG)")

    if not st.session_state.token:
        st.warning("Login required.")
        st.stop()

    allowed, _ = require_access_or_redirect()

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

    allowed, _ = require_access_or_redirect()

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