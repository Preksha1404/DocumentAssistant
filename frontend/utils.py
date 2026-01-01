import streamlit as st
import requests

API_BASE = "https://documentassistant-production.up.railway.app"

# ---------------- UTIL FUNCTIONS -----------------
def api_post(path, json=None, files=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if files:
            res = requests.post(API_BASE + path, files=files, headers=headers)
        else:
            res = requests.post(API_BASE + path, json=json, headers=headers)
        if res.status_code >= 400:
            st.error(res.text)
            return None
        return res.json()
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def api_get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        res = requests.get(API_BASE + path, headers=headers)
        if res.status_code >= 400:
            st.error(res.text)
            return None
        return res.json()
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None
    
def require_access_or_redirect():
    sub = api_get("/billing/me/subscription", token=st.session_state.token)
    if not sub:
        return False, None

    status = sub.get("subscription_status")
    if status not in ["trialing", "active"]:
        st.warning("🔒 Access requires an active trial or subscription.")
        st.markdown("👉 Go to **Home** to start your free trial.")
        st.stop()

    return True, sub