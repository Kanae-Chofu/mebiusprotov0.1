#全体を統合する部門
import streamlit as st
from modules import board, karitunagari, chat

st.set_page_config(page_title="メビウス統合プロトタイプ", layout="wide")
st.title("🌌 メビウス α版：関係性のグラデーション空間")

tab1, tab2, tab3 = st.tabs(["掲示板", "仮つながりスペース", "1:1チャット"])

with tab1:
    board.render()

with tab2:
    karitunagari.render()

with tab3:
    chat.render()