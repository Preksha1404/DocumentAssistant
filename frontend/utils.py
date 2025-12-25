import os
import streamlit as st
import requests

if os.getenv("ENV") == "production":
    API_BASE ="https://documentassistant-production.up.railway.app"
else:
    API_BASE = "http://localhost:8000"

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