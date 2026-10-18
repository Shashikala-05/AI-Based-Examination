"""
Milestone 2 — ExamPortal (alignment-fixed version)
UI: Streamlit | Database: SQLite
Roles: Student, Teacher, Admin
"""

import os
import re
import hmac
import hashlib
import secrets
import sqlite3
from pathlib import Path

import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="ExamPortal | Authentication",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "exam_portal.db"


# ============================================================
# 2. CSS — CONSISTENT SPACING, WIDTHS, AND ALIGNMENT
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
      --ink: #17233f;
      --muted: #667085;
      --primary: #4f46e5;
      --cyan: #0891b2;
      --border: #e4e9f2;
    }

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp {
      background:
        radial-gradient(ellipse at 5% 5%, rgba(99,102,241,.10), transparent 28%),
        radial-gradient(ellipse at 95% 95%, rgba(6,182,212,.09), transparent 25%),
        #f5f7fc;
      color: var(--ink);
    }
    #MainMenu, footer, header { visibility: hidden; }

    /* Keep the overall page centered and prevent oversized content. */
    .block-container {
      max-width: 1160px;
      padding: 1.35rem 1.5rem 2.5rem;
    }

    .brand-row {
      display:flex; align-items:center; justify-content:space-between;
      gap:16px; margin:0 0 24px;
    }
    .brand-left { display:flex; align-items:center; gap:12px; }
    .brand-mark {
      width:44px; height:44px; flex:0 0 44px;
      display:flex; align-items:center; justify-content:center;
      border-radius:14px; color:white; font-size:22px;
      background:linear-gradient(135deg,#6366f1,#06b6d4);
      box-shadow:0 8px 20px rgba(79,70,229,.22);
    }
    .brand-name { color:#172554; font:800 1.2rem 'Manrope',sans-serif; line-height:1.15; }
    .brand-caption { color:#77839a; font-size:.78rem; margin-top:4px; }
    .secure-tag {
      padding:9px 13px; border:1px solid #dfe6f1; border-radius:100px;
      background:rgba(255,255,255,.8); color:#5d6a80; font-size:.78rem; font-weight:600;
      white-space:nowrap;
    }

    /* The two columns start at the same vertical position. */
    [data-testid="stHorizontalBlock"] { align-items: stretch; gap: 1.25rem; }
    [data-testid="column"] { min-width: 0; }

    /* Style actual Streamlit bordered containers (not decorative HTML wrappers). */
    div[data-testid="stVerticalBlockBorderWrapper"] {
      border:1px solid #e4e9f2 !important;
      border-radius:24px !important;
      background:rgba(255,255,255,.96) !important;
      box-shadow:0 18px 45px rgba(23,37,84,.065);
      padding:0 !important;
    }

    .hero-content { padding:27px 26px 25px; }
    .hero-card-title {
      color:white; font:800 clamp(2rem,2.8vw,2.85rem)/1.13 'Manrope',sans-serif;
      letter-spacing:-.045em; margin:20px 0 14px;
    }
    .hero-card-copy {
      color:rgba(255,255,255,.84); font-size:.96rem; line-height:1.75;
      margin:0 0 23px;
    }
    .hero-badge {
      display:inline-block; border:1px solid rgba(255,255,255,.25);
      border-radius:100px; padding:7px 11px; background:rgba(255,255,255,.12);
      color:#f7f8ff; font-size:.73rem; font-weight:700; letter-spacing:.06em;
      text-transform:uppercase;
    }
    .hero-feature {
      display:flex; align-items:center; gap:12px; padding:13px;
      border:1px solid rgba(255,255,255,.16); background:rgba(255,255,255,.10);
      border-radius:14px; margin-top:11px;
    }
    .hero-feature-icon {
      width:38px; height:38px; flex:0 0 38px; display:flex;
      align-items:center; justify-content:center; border-radius:11px;
      background:rgba(255,255,255,.15); font-size:18px;
    }
    .hero-feature-title { color:white; font-size:.88rem; font-weight:700; }
    .hero-feature-text { color:rgba(255,255,255,.73); font-size:.77rem; line-height:1.45; margin-top:3px; }

    .panel-title { font:800 1.75rem 'Manrope',sans-serif; color:#172554; letter-spacing:-.04em; }
    .panel-subtitle { color:#748096; font-size:.9rem; line-height:1.6; margin:5px 0 18px; }
    .form-section-label {
      color:#52627c; font-size:.73rem; font-weight:800; letter-spacing:.09em;
      text-transform:uppercase; margin:10px 0 8px;
    }
    .field-help { color:#7a879b; font-size:.77rem; line-height:1.5; }

    /* Make text inputs and select boxes use the same shape and height. */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
      min-height:44px !important;
      border-radius:10px !important;
      border-color:#dce3ef !important;
      background:#fff !important;
    }
    div[data-baseweb="input"] input { font-size:.9rem; }
    label, [data-testid="stWidgetLabel"] p {
      color:#34415a !important; font-size:.82rem !important; font-weight:600 !important;
    }
    div[data-testid="stForm"] { border:0 !important; padding:0 !important; }
    div[data-testid="stFormSubmitButton"] > button,
    div.stButton > button {
      width:100%; min-height:45px; border:0; border-radius:11px;
      background:linear-gradient(100deg,#4f46e5,#0787a8);
      color:white; font-weight:700;
      box-shadow:0 8px 18px rgba(79,70,229,.16);
      transition:transform .15s ease, box-shadow .15s ease;
    }
    div[data-testid="stFormSubmitButton"] > button:hover,
    div.stButton > button:hover {
      color:white; transform:translateY(-1px);
      box-shadow:0 12px 22px rgba(79,70,229,.22);
    }
    div[role="radiogroup"] { gap:8px; }
    div[role="radiogroup"] label {
      border:1px solid #e1e6f0; border-radius:10px;
      background:#f8faff; padding:7px 10px;
    }
    .footnote { text-align:center; color:#8993a6; font-size:.74rem; padding-top:13px; }

    @media(max-width: 850px) {
      .block-container { padding:1rem .8rem 2rem; }
      .brand-caption { display:none; }
      .secure-tag { display:none; }
      .hero-card-title { font-size:2rem; }
      .hero-content { padding:23px 20px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. SQLITE DATABASE
# ============================================================
def get_connection():
    """Create a SQLite connection with named-column access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the users table and unique student roll-number index."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                role TEXT NOT NULL CHECK(role IN ('student','teacher','admin')),
                institute TEXT,
                roll_number TEXT,
                class_year TEXT,
                department TEXT,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_student_roll
            ON users(roll_number)
            WHERE role = 'student' AND roll_number IS NOT NULL
            """
        )


initialize_database()


# ============================================================
# 4. PASSWORD SECURITY
# ============================================================
def hash_password(password, salt=None):
    """Return a salted password hash; the plain password is never saved."""
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 310_000
    )
    return digest.hex(), salt.hex()


def password_matches(password, saved_hash, saved_salt):
    """Verify a password using constant-time comparison."""
    calculated_hash, _ = hash_password(password, bytes.fromhex(saved_salt))
    return hmac.compare_digest(calculated_hash, saved_hash)


# ============================================================
# 5. DATABASE OPERATIONS
# ============================================================
def create_user(
    first_name, last_name, email, role, password,
    institute=None, roll_number=None, class_year=None, department=None
):
    """Create a user after hashing the password."""
    password_hash, password_salt = hash_password(password)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    first_name, last_name, email, role, institute, roll_number,
                    class_year, department, password_hash, password_salt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    first_name.strip(), last_name.strip(), email.strip().lower(),
                    role, institute.strip() if institute else None,
                    roll_number.strip() if roll_number else None,
                    class_year.strip() if class_year else None,
                    department.strip() if department else None,
                    password_hash, password_salt,
                ),
            )
        return True, "Account created successfully. You can now sign in."
    except sqlite3.IntegrityError as exc:
        message = str(exc).lower()
        if "users.email" in message:
            return False, "This email address is already registered."
        if "users.roll_number" in message:
            return False, "This student roll number is already registered."
        return False, "Could not create the account. Please check the details."


def find_user(email):
    """Find an account by email."""
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
            (email.strip().lower(),),
        ).fetchone()


def count_users(role=None):
    """Count users, optionally filtering by role."""
    with get_connection() as connection:
        if role:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM users WHERE role = ?", (role,)
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM users"
            ).fetchone()
    return row["total"]


# ============================================================
# 6. SESSION STATE
# ============================================================
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"


# ============================================================
# 7. TOP HEADER
# ============================================================
st.markdown(
    """
    <div class="brand-row">
      <div class="brand-left">
        <div class="brand-mark">🎓</div>
        <div>
          <div class="brand-name">ExamPortal</div>
          <div class="brand-caption">Smart assessment · Better learning</div>
        </div>
      </div>
      <div class="secure-tag">🔒 &nbsp; Secure academic access</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 8. MAIN TWO-COLUMN LAYOUT
# ============================================================
left_col, right_col = st.columns([1, 1], gap="large", vertical_alignment="top")


# -------------------------- LEFT: HERO CARD -----------------
with left_col:
    # Use a real Streamlit container with a border. Unlike an HTML div,
    # this correctly contains the Streamlit elements and supports styling.
    with st.container(border=True):
        st.markdown(
            """
            <div class="hero-content" style="
                border-radius:20px;
                background:linear-gradient(145deg,#1e1b4b 0%,#4338ca 54%,#0787a8 100%);
                color:white;
            ">
              <div class="hero-badge">✦ &nbsp; YOUR LEARNING SPACE</div>
              <div class="hero-card-title">Learning starts with the right connection.</div>
              <div class="hero-card-copy">
                One secure portal for your academic community. Sign in to continue
                your journey, manage assessments, and stay connected to learning.
              </div>

              <div class="hero-feature">
                <div class="hero-feature-icon">🎯</div>
                <div>
                  <div class="hero-feature-title">Built around your role</div>
                  <div class="hero-feature-text">Dedicated access for students, teachers and admins.</div>
                </div>
              </div>
              <div class="hero-feature">
                <div class="hero-feature-icon">🛡️</div>
                <div>
                  <div class="hero-feature-title">Security comes first</div>
                  <div class="hero-feature-text">Passwords are hashed before they are stored.</div>
                </div>
              </div>
              <div class="hero-feature">
                <div class="hero-feature-icon">📚</div>
                <div>
                  <div class="hero-feature-title">Ready to grow with your project</div>
                  <div class="hero-feature-text">Exams, results and user management can be added next.</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -------------------------- RIGHT: AUTH CARD ----------------
with right_col:
    with st.container(border=True):
        user = st.session_state.logged_in_user

        # Logged-in view
        if user:
            st.markdown('<div class="panel-title">Welcome back 👋</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="panel-subtitle">Signed in as {user["role"].title()}.</div>',
                unsafe_allow_html=True,
            )
            st.success("Login successful.")

            st.markdown("#### Account details")
            st.write(f"**Name:** {user['first_name']} {user['last_name']}")
            st.write(f"**Email:** {user['email']}")
            st.write(f"**Role:** {user['role'].title()}")

            st.markdown("#### Your workspace")
            if user["role"] == "student":
                st.write(f"**Institute:** {user['institute'] or '—'}")
                st.write(f"**Roll number:** {user['roll_number'] or '—'}")
                st.write(f"**Class / Year:** {user['class_year'] or '—'}")
                st.info("Student exam and results modules can be connected here.")
            elif user["role"] == "teacher":
                st.write(f"**Department:** {user['department'] or '—'}")
                st.info("Teacher question and assessment modules can be connected here.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Students", count_users("student"))
                c2.metric("Teachers", count_users("teacher"))
                c3.metric("Admins", count_users("admin"))

            st.divider()
            if st.button("Log out", use_container_width=True):
                st.session_state.logged_in_user = None
                st.session_state.auth_mode = "Login"
                st.rerun()

        # Login / signup view
        else:
            st.markdown('<div class="panel-title">Your account</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="panel-subtitle">Sign in or create an account to continue.</div>',
                unsafe_allow_html=True,
            )

            mode = st.radio(
                "Choose an action",
                ["Login", "Sign up"],
                horizontal=True,
                index=0 if st.session_state.auth_mode == "Login" else 1,
                label_visibility="collapsed",
                key="auth_mode_selector",
            )
            st.session_state.auth_mode = mode
            st.divider()

            # ----------------------- LOGIN FORM -----------------------
            if mode == "Login":
                st.markdown('<div class="form-section-label">WELCOME BACK</div>', unsafe_allow_html=True)

                with st.form("login_form"):
                    role = st.selectbox("Login as", ["Student", "Teacher", "Admin"])
                    email = st.text_input("Email address", placeholder="name@institute.edu")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    login_clicked = st.form_submit_button("Sign in securely", use_container_width=True)

                if login_clicked:
                    if not email.strip() or not password:
                        st.error("Enter your email address and password.")
                    else:
                        record = find_user(email)
                        if (
                            record
                            and record["role"] == role.lower()
                            and password_matches(password, record["password_hash"], record["password_salt"])
                        ):
                            st.session_state.logged_in_user = dict(record)
                            st.rerun()
                        else:
                            st.error("Email, password, or role is incorrect.")

                st.markdown(
                    '<div class="field-help">Use the same role you selected when creating your account.</div>',
                    unsafe_allow_html=True,
                )

            # ----------------------- SIGNUP FORM ----------------------
            else:
                st.markdown('<div class="form-section-label">CREATE YOUR ACCOUNT</div>', unsafe_allow_html=True)

                # Role selection is outside the form so switching role updates
                # which fields are displayed immediately.
                signup_role = st.selectbox(
                    "Register as",
                    ["Student", "Teacher", "Admin"],
                    key="signup_role_fixed",
                )
                role_key = signup_role.lower()

                with st.form("signup_form"):
                    # Every row uses the same 50/50 column ratio for alignment.
                    name_left, name_right = st.columns(2, gap="medium")
                    with name_left:
                        first_name = st.text_input("First name", placeholder="First name")
                    with name_right:
                        last_name = st.text_input("Last name", placeholder="Last name")

                    email = st.text_input("Email address", placeholder="name@institute.edu")

                    institute = None
                    roll_number = None
                    class_year = None
                    department = None
                    admin_code = None

                    if role_key == "student":
                        student_left, student_right = st.columns(2, gap="medium")
                        with student_left:
                            institute = st.text_input("Institute", placeholder="College / institute")
                        with student_right:
                            roll_number = st.text_input("Roll number", placeholder="e.g. MCA2026-014")
                        class_year = st.selectbox(
                            "Class / Year",
                            ["1st Year", "2nd Year", "3rd Year", "4th Year", "Final Year", "Other"],
                        )
                    elif role_key == "teacher":
                        department = st.text_input("Department", placeholder="e.g. Computer Science")
                    else:
                        st.warning("Admin signup requires a private setup code.")
                        admin_code = st.text_input("Admin setup code", type="password")

                    password_left, password_right = st.columns(2, gap="medium")
                    with password_left:
                        password = st.text_input("Password", type="password", placeholder="At least 8 characters")
                    with password_right:
                        confirm_password = st.text_input("Confirm password", type="password", placeholder="Repeat password")

                    st.caption("Use at least 8 characters. Passwords are stored as secure hashes.")
                    signup_clicked = st.form_submit_button("Create account", use_container_width=True)

                if signup_clicked:
                    if not all([
                        first_name.strip(), last_name.strip(), email.strip(),
                        password, confirm_password
                    ]):
                        st.error("Please complete all required fields.")
                    elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
                        st.error("Enter a valid email address.")
                    elif len(password) < 8:
                        st.error("Password must contain at least 8 characters.")
                    elif password != confirm_password:
                        st.error("Password and confirm password do not match.")
                    elif role_key == "student" and not all([
                        (institute or "").strip(), (roll_number or "").strip()
                    ]):
                        st.error("Enter your institute and roll number.")
                    elif role_key == "teacher" and not (department or "").strip():
                        st.error("Enter your department.")
                    elif role_key == "admin" and (
                        not os.getenv("ADMIN_SIGNUP_CODE")
                        or not hmac.compare_digest(
                            admin_code or "", os.getenv("ADMIN_SIGNUP_CODE", "")
                        )
                    ):
                        st.error(
                            "Admin setup code is incorrect or not configured. "
                            "Set ADMIN_SIGNUP_CODE before starting the app."
                        )
                    else:
                        success, message = create_user(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            role=role_key,
                            password=password,
                            institute=institute,
                            roll_number=roll_number,
                            class_year=class_year,
                            department=department,
                        )
                        if success:
                            st.success(message)
                            st.info("Select Login above to sign in.")
                        else:
                            st.error(message)

            st.markdown(
                '<div class="footnote">ExamPortal · Milestone 2 · SQLite authentication</div>',
                unsafe_allow_html=True,
            )
