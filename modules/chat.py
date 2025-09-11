import streamlit as st
import sqlite3
import bcrypt
from streamlit_autorefresh import st_autorefresh

# 🌙 ダークモード固定＋背景色変更
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    div[data-testid="stHeader"] {
        background-color: #000000;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    input, textarea {
        background-color: #1F2F54 !important;
        color: #FFFFFF !important;
    }
    button {
        background-color: #426AB3 !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# データベース初期化
def init_db():
    conn = sqlite3.connect("db/chat.db")  # ← db/ に移動している場合はパス変更
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receiver TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS friends (
                    user TEXT,
                    friend TEXT,
                    UNIQUE(user, friend))''')
    conn.commit()
    conn.close()

# 各機能関数（register_user, login_user, save_message, get_messages, add_friend, get_friends）←そのままでOK
# ユーザー登録
def register_user(username, password):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ログイン
def login_user(username, password):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode(), result[0]):
        return True
    return False

# メッセージ保存
def save_message(sender, receiver, message):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (sender, receiver, message))
    conn.commit()
    conn.close()

# メッセージ取得
def get_messages(user, partner):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute('''SELECT sender, message, timestamp FROM messages 
                 WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) 
                 ORDER BY timestamp''',
              (user, partner, partner, user))
    messages = c.fetchall()
    conn.close()
    return messages

# 友達追加
def add_friend(user, friend):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO friends (user, friend) VALUES (?, ?)", (user, friend))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# 友達一覧取得
def get_friends(user):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT friend FROM friends WHERE user = ?", (user,))
    friends = [row[0] for row in c.fetchall()]
    conn.close()
    return friends

# ✅ 統合用の render 関数
def render():
    init_db()
    st.title("1対1チャットSNSメビウス（α版）")
    st_autorefresh(interval=5000, key="chat_autorefresh")

    if "username" not in st.session_state:
        st.session_state.username = None
    if "partner" not in st.session_state:
        st.session_state.partner = None

    menu = st.radio("操作を選択してください", ["新規登録", "ログイン"], horizontal=True)

    if menu == "新規登録":
        st.subheader("🆕 新規登録")
        new_user = st.text_input("ユーザー名を入力")
        new_pass = st.text_input("パスワードを入力", type="password")
        if st.button("登録", use_container_width=True):
            if register_user(new_user, new_pass):
                st.success("登録成功！ログインしてください")
            else:
                st.error("このユーザー名は既に使われています")

    elif menu == "ログイン":
        st.subheader("🔐 ログイン")
        user = st.text_input("ユーザー名")
        pw = st.text_input("パスワード", type="password")
        if st.button("ログイン", use_container_width=True):
            if login_user(user, pw):
                st.session_state.username = user
                st.success(f"{user} でログインしました！")
            else:
                st.error("ユーザー名かパスワードが違います")

    if st.session_state.username:
        st.divider()
        st.subheader("💬 チャット画面")
        st.write(f"ログイン中ユーザー: `{st.session_state.username}`")

        with st.expander("👥 友達一覧を表示／非表示", expanded=True):
            friends = get_friends(st.session_state.username)
            if friends:
                for f in friends:
                    st.markdown(f"- `{f}`")
            else:
                st.info("まだ友達はいません。ユーザー名を入力して友達追加してください。")

        partner = st.text_input("チャット相手のユーザー名を入力", st.session_state.partner or "")
        if partner:
            st.session_state.partner = partner
            st.write(f"チャット相手: `{partner}`")

            if st.button("このユーザーを友達に追加", use_container_width=True):
                if add_friend(st.session_state.username, partner):
                    st.success(f"{partner} を友達に追加しました！")
                else:
                    st.info(f"{partner} はすでに友達に追加されています")

        if st.session_state.partner:
            messages = get_messages(st.session_state.username, st.session_state.partner)
            for sender, msg, _ in messages:
                if sender == st.session_state.username:
                    st.markdown(
                        f"""
                        <div style='text-align: right; margin: 5px 0;'>
                            <span style='background-color:#1F2F54; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%;'>
                                {msg}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div style='text-align: left; margin: 5px 0;'>
                            <span style='background-color:#426AB3; color:#FFFFFF; padding:8px 12px; border-radius:10px; display:inline-block; max-width:80%; border:1px solid #ccc;'>
                                {msg}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # ✉️ メッセージ送信（← 佳苗さんが言っていた末尾）
            new_message = st.chat_input("メッセージを入力")
            if new_message:
                save_message(st.session_state.username, st.session_state.partner, new_message)
                st.rerun()