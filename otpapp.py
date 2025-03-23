import streamlit as st
import time
import base64
import random
import smtplib
import re
from datetime import datetime
from email.mime.text import MIMEText
from streamlit_autorefresh import st_autorefresh
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- CONFIG ----------------
OTP_VALIDITY_DURATION = 60  # seconds
MAX_ATTEMPTS = 3

# 3 background images
login_bg = "login.png"    # for the login page
otp_bg = "otpver.png"     # for the OTP screen
success_bg = "osucc.png"  # for the success screen

SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")

# -----------------------------------------------------------------
#                GLOBAL STYLE INJECTION
# -----------------------------------------------------------------
st.markdown("""
<style>

/* Dark yellow for warnings */
.warning-msg {
    color: #ff5b00;
    font-weight: bold;
    font-size: 15px;
    padding: 5px;
    margin: 3px auto;
    display: block;
    white-space: nowrap;
}

/* bright red for errors */
.error-msg {
    color: #ff000d;
    font-weight: bold;
    font-size: 15px;
    padding: 5px;
    margin: 3px auto;
    display: block;
    white-space: nowrap;
}

/* Green for success */
.success-msg {
    color: #4AA600;
    font-weight: bold;
    padding: 5px;
    font-size: 15px;
    margin: 3px auto;
    display: block;
    white-space: nowrap;
}

.mail-sent {
    color: #4AA600 !important;
    font-size: 15px !important;
    font-weight: bold !important;
    padding: 5px !important;
    border-radius: 6px !important;
    margin-bottom: 5px !important;
    display: block;
    white-space: nowrap;
}

.resend-label {
    color: #fe01b1 !important;
    font-size: 17px !important;
    font-weight: bold !important;
    padding: 5px !important;
    border-radius: 6px !important;
    display: block !important;
    margin-bottom: 8px !important;
    white-space: nowrap;
}

.reset-label {
    color: #bf00ff !important; 
    font-size: 17px !important;
    font-weight: bold !important;
    padding: 5px !important;
    border-radius: 8px !important;
    display: block !important;
    margin-bottom: 8px !important;
    white-space: nowrap;
}

/* Textboxes => more vibrant look + increased width */
div[data-baseweb="input"] {
    box-sizing: border-box;
    border: 2px solid #00CED1 !important;
    border-radius: 10px !important;
    background: #f0fff0 !important;
    color: #000 !important;
    height: 40px !important;
    line-height: 30px !important;
    padding: 0 8px !important;
    font-size: 26px !important;
    margin: 3px 0 !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
    width: 300px !important;
}
div[data-baseweb="input"]:hover {
    box-shadow: 0 0 6px #00CED1 !important;
}
.stTextInput label {
    color: #4169E1 !important;
    font-weight: bold !important;
    font-size: 25px !important;
    margin-bottom: 5px !important;
}

/* Buttons =>  */
div.stButton > button {
    background: linear-gradient(135deg, #12f0b5, #FFA500) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    border-radius: 10px !important;
    padding: 13px 20px !important;
    border: none !important;
    height: 50px !important; 
    font-size: 20px !important;
    cursor: pointer !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    transition: 0.4s ease-in-out !important; /* Slightly longer transition for shimmer */
    margin: 10px auto !important;
    display: block !important;
    width: 150px !important;
    position: relative !important;      /* Needed for shimmer effect */
    overflow: hidden !important;        /* Hide the shimmer overflow */
}

/* Shimmer overlay */
div.stButton > button::after {
    content: "" !important;
    position: absolute !important;
    top: 0 !important;
    left: -75px !important;
    width: 50px !important;
    height: 100% !important;
    background: linear-gradient(
        to right, 
        rgba(255,255,255,0),
        rgba(255,255,255,0.6),
        rgba(255,255,255,0)
    ) !important;
    transform: skewX(-20deg) !important;
    transition: left 0.7s ease !important;
}

/* Hover => flip gradient, scale, and shimmer slides across */
div.stButton > button:hover {
    background: linear-gradient(135deg, #FFA500, #12f0b5) !important;
    transform: scale(1.05) !important;
}

div.stButton > button:hover::after {
    left: 200% !important;  /* Move shimmer across the button */
}

/* Title backgrounds */
.login-title-container {
    background: linear-gradient(135deg, #11ffe3, #F08080) !important;
}
.otp-title-container {
    background: linear-gradient(135deg, #56deff, #f2ff59) !important;
}
.success-title-container {
    background: linear-gradient(135deg, #FF1493, #FFB6C1) !important;
}

/* Inline buttons */
.inline-buttons {
    width: 100%;
    text-align: center;
}
.inline-buttons > div.stButton {
    display: inline-block;
    vertical-align: middle;
    width: 32%;
    margin: 5px;
}

/* Additional styling for success title to restrict its width and wrap long names */
.success-title {
    color: #ffffff !important;
    font-weight: 800 !important;
    margin: 0 !important;
    max-width: 80%;
    overflow-wrap: break-word;
    text-shadow: none !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------
def init_session():
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = True
        st.session_state["otp"] = None
        st.session_state["otp_sent"] = False
        st.session_state["otp_sent_time"] = None
        st.session_state["attempts"] = 0
        st.session_state["verified"] = False
        st.session_state["timer_expired"] = False
        st.session_state["time_left"] = 0
        st.session_state["name"] = ""
        st.session_state["email"] = ""
        st.session_state["error_msg"] = ""
        st.session_state["success_msg"] = ""
        st.session_state["warning_msg"] = ""
        st.session_state["max_attempts_reached"] = False
        st.session_state["timer_out"] = False
        st.session_state["otp_input"] = ""
        st.session_state["otp_expiry"] = None  # Stores OTP expiry timestamp
        st.session_state["just_verified"] = False

def reset_state():
    """Reset relevant states except name/email."""
    st.session_state["otp"] = None
    st.session_state["otp_sent"] = False
    st.session_state["otp_sent_time"] = None
    st.session_state["attempts"] = 0
    st.session_state["verified"] = False
    st.session_state["timer_expired"] = False
    st.session_state["time_left"] = 0
    st.session_state["error_msg"] = ""
    st.session_state["success_msg"] = ""
    st.session_state["warning_msg"] = ""
    st.session_state["max_attempts_reached"] = False
    st.session_state["timer_out"] = False

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

# New function to validate name: must start with a letter and contain only letters and spaces
def is_valid_name(name):
    pattern = r"^[A-Za-z][A-Za-z ]*$"
    return bool(re.match(pattern, name))

def send_otp(email, name):
    """Generate & send OTP, then rerun to show countdown."""
    otp = str(random.randint(100000, 999999))
    st.session_state["otp"] = otp
    st.session_state["otp_sent_time"] = datetime.now()
    st.session_state["attempts"] = 0
    st.session_state["timer_expired"] = False
    st.session_state["verified"] = False
    st.session_state["error_msg"] = ""
    st.session_state["success_msg"] = ""
    st.session_state["warning_msg"] = ""
    st.session_state["max_attempts_reached"] = False
    st.session_state["timer_out"] = False

    subject = "Your OTP Code"
    body = (
        f"Hello {name},\n\n"
        f"Your OTP code is: {otp}\n"
        f"This code will expire in {OTP_VALIDITY_DURATION} seconds."
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        st.session_state["otp_sent"] = True
        st.rerun()
    except Exception as e:
        st.session_state["error_msg"] = f"⚠️ Error In Sending OTP: {e}"
        st.session_state["otp_sent"] = False

def verify_otp(user_otp):
    """Check user_otp. If correct => set verified => success page."""
    if not st.session_state["otp"] or st.session_state["timer_expired"]:
        st.session_state["error_msg"] = "⏳ OTP expired/not generated. Request new OTP."
        return

    elapsed = (datetime.now() - st.session_state["otp_sent_time"]).seconds
    if elapsed > OTP_VALIDITY_DURATION:
        st.session_state["error_msg"] = "⏰ OTP has expired.To continue, choose an option below"
        st.session_state["timer_out"] = True
        st.session_state["timer_expired"] = True
        st.session_state["otp_sent"] = False
        return

    if user_otp == st.session_state["otp"]:
        st.session_state["error_msg"] = ""
        st.session_state["verified"] = True
        st.session_state["just_verified"] = True 
        st.rerun()
    else:
        st.session_state["attempts"] += 1
        remaining = MAX_ATTEMPTS - st.session_state["attempts"]
        if remaining > 0:
            st.session_state["error_msg"] = f"❌ Incorrect OTP! {remaining} Attempts Left."
        else:
            st.session_state["error_msg"] = "🚫 Too Many Failed Attempts!!! To Continue, Click ."
            st.session_state["max_attempts_reached"] = True

def set_background(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()

    if image_path == login_bg:
        bg_size = "70% auto"
        bg_position = "center center"
    elif image_path == otp_bg:
        bg_size = "70% auto"
        bg_position = "center center"
    elif image_path == success_bg:
        bg_size = "70% auto"
        bg_position = "center center"
    else:
        bg_size = "cover"
        bg_position = "center center"

    st.markdown(
        f"""
        <style>
        .stApp {{
            margin-top: 0px;
            background: url("data:image/png;base64,{encoded_string}") no-repeat {bg_position};
            background-size: {bg_size};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def render_login_form():
    if st.session_state["otp_sent"] and not st.session_state["verified"]:
        render_otp_screen()
        return

    disable_fields = (
        st.session_state["otp_sent"]
        and not st.session_state["max_attempts_reached"]
        and not st.session_state["timer_out"]
    )

    st.session_state["name"] = st.text_input(
        "**Enter your Name:**",
        value=st.session_state.get("name", ""),
        max_chars=20,  # Restrict user to 20 characters
        disabled=disable_fields,
        key="name_input"
    )
    st.session_state["email"] = st.text_input(
        "**Enter your Email:**",
        value=st.session_state.get("email", ""),
        disabled=disable_fields,
        key="email_input"
    )

    if st.button("Send OTP", disabled=disable_fields, key="send_otp_button"):
        # Clear any previous messages
        st.session_state["warning_msg"] = ""
        st.session_state["error_msg"] = ""

        name_filled = bool(st.session_state["name"].strip())
        email_filled = bool(st.session_state["email"].strip())
        
        if not name_filled and not email_filled:
           st.session_state["warning_msg"] = "⚠️ Please Enter Both Name & Email."
        elif not name_filled:
           st.session_state["warning_msg"] = "⚠️ Please Enter Your Name."
        elif not is_valid_name(st.session_state["name"]):
           st.session_state["warning_msg"] = "⚠️ Enter Valid Name. Must Start With Letter.<br> ( * ) Only Letters And Spaces Allowed."
        elif not email_filled:
           st.session_state["warning_msg"] = "⚠️ Please Enter Your Email."
        elif not is_valid_email(st.session_state["email"]):
           st.session_state["error_msg"] = " ❌ Please Enter Valid Email Address."
        else:
           send_otp(st.session_state["email"], st.session_state["name"])
            
    if st.session_state.get("error_msg"):
        st.markdown(
            f"<div class='error-msg'>{st.session_state['error_msg']}</div>",
            unsafe_allow_html=True
        )

def render_otp_screen():
    if st.session_state["verified"]:
        final_success_screen()
        return

    st.markdown("""
        <style>
            .otp-title-container {
                width: 330px !important;
                text-align: left !important;
                padding: 10px;
                border-radius: 12px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.5);
                margin-top: -8px !important; /* Put the title at the very top */
                margin-bottom: 15px !important; /* If you also want no bottom margin */
            }
            .otp-title {
                color: #b5651d;
                font-size: 25px;
                font-weight: bold;
                text-shadow: 1px 1px 5px rgba(255, 255, 255, 0.5);
                margin: 0;
            }
            .error-container {
                min-height: 6px; /* Larger space to handle bigger error text */
                margin-bottom: 0;
                text-align: left;
            }
        </style>
    """, unsafe_allow_html=True)

    # Title at the top
    st.markdown('<div class="otp-title-container"><div class="otp-title">🔒 OTP VERIFICATION PAGE</div></div>', unsafe_allow_html=True)

    # Error container placeholder
    error_container = st.empty()
    if st.session_state.get("error_msg"):
        error_html = f"""
        <div class="error-container">
            <span class="error-msg">{st.session_state["error_msg"]}</span>
        </div>
        """
        error_container.markdown(error_html, unsafe_allow_html=True)
    else:
        error_container.markdown("<div class='error-container'></div>", unsafe_allow_html=True)

    if st.session_state["timer_expired"] or st.session_state["max_attempts_reached"]:
        st.session_state["otp_input"] = ""
        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="resend-label">
                🔄 Need New OTP ? Click Resend
            </div>
            <div class="reset-label">
                🔙 Return To Login ? Click Reset
            </div>
        """, unsafe_allow_html=True)
        try:
            col_resend, col_reset = st.columns(2)
        except Exception:
            col_resend, col_reset = None, None

        if col_resend and col_reset:
            with col_resend:
                if st.button("Resend OTP", key="resend_button"):
                    st.session_state["timer_expired"] = False
                    st.session_state["max_attempts_reached"] = False
                    send_otp(st.session_state["email"], st.session_state["name"])
                    st.session_state["error_msg"] = ""
                    st.rerun()
                    return
            with col_reset:
                if st.button("Reset", key="reset_button"):
                    reset_state()
                    st.session_state["name"] = ""
                    st.session_state["email"] = ""
                    st.session_state["otp_input"] = ""
                    st.rerun()
                    return
        else:
            if st.button("Resend OTP", key="resend_button"):
                st.session_state["timer_expired"] = False
                st.session_state["max_attempts_reached"] = False
                st.session_state["otp_input"] = ""
                send_otp(st.session_state["email"], st.session_state["name"])
                st.session_state["error_msg"] = ""
                st.rerun()
                return
            if st.button("Reset", key="reset_button"):
                reset_state()
                st.session_state["name"] = ""
                st.session_state["email"] = ""
                st.session_state["otp_input"] = ""
                st.rerun()
                return
        return

    if st.session_state.get("otp_sent") and st.session_state.get("email"):
        st.markdown(f'<div class="mail-sent" style="text-align: left;">✅ Mail Sent to {st.session_state["email"]}</div>', unsafe_allow_html=True)

    timer_placeholder = st.empty()
    if st.session_state.get("otp_sent") and not st.session_state["verified"]:
        elapsed = (datetime.now() - st.session_state["otp_sent_time"]).seconds
        time_left = OTP_VALIDITY_DURATION - elapsed
        if time_left > 0:
            mins, secs = divmod(time_left, 60)
            timer_placeholder.markdown(
                f"<div style='text-align: left; font-size: 15px; padding: 8px; color: #ff471a; font-weight: bold;'> ⏳ Time left: {mins:02d}:{secs:02d}</div>",
                unsafe_allow_html=True
            )
        else:
            st.session_state["error_msg"] = "⏰ OTP Expired !! To Continue Request Again."
            st.session_state["timer_expired"] = True
            st.session_state["timer_out"] = True
            timer_placeholder.empty()
            st.rerun()

    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
    st.session_state["otp_input"] = st.text_input("**Enter your OTP:**", max_chars=6, value="", key="otp_textbox")
    if st.button("Verify OTP", key="verify_button"):
        user_otp = st.session_state["otp_input"].strip()
        if not user_otp:
            st.session_state["error_msg"] = "⚠️ Please Enter The OTP First!"
        elif not user_otp.isdigit() or len(user_otp) != 6:
            st.session_state["error_msg"] = "⚠️ OTP Must Be 6 Numeric Digits."
        else:
            verify_otp(user_otp)


def final_success_screen():
    if st.session_state.get("just_verified", False):
        st.balloons()
        st.session_state["just_verified"] = False

    username = st.session_state["name"]

    
    st.markdown(f"""
    <style>
    .title-wrapper {{
        margin: 50px auto;
        top: 120px;
        display: flex;
        flex-direction: column;
        gap: 40px;
        z-index: 9999;
    }}
    @keyframes slideInRight {{
      0% {{
        transform: translateX(100%);
        opacity: 0;
      }}
      100% {{
        transform: translateX(0);
        opacity: 1;
      }}
    }}
    .title-box {{
        width: 500px;
        align-items: center; 
        padding: 10x;
        border-radius: 10px;
        color: #ffffff;
        font-size: 26px;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 170, 255, 0.6);
        border:3px solid #00aaff;
        animation: slideInRight 0.8s ease forwards;
    }}
    .box1 {{
        background: linear-gradient(135deg, #FFA500, #FF13F0);
        animation-delay: 0.2s;
    }}
    .box2 {{
        background: linear-gradient(135deg, #32CD32, #02CCFE);
        animation-delay: 0.2s;
    }}

    /* Balloons & party icon container */
    .balloons {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
    }}
    .balloon {{
        position: absolute;
        bottom: -150px;
        width: 40px;
        height: 60px;
        border-radius: 50%;
        animation: floatUp 7s ease-in infinite;
    }}
    @keyframes floatUp {{
        0% {{
            transform: translateY(0) scale(1);
            opacity: 1;
        }}
        95% {{
            opacity: 1;
        }}
        100% {{
            transform: translateY(-120vh) scale(1.1);
            opacity: 0;
        }}
    }}
    .balloon1 {{ background: #ff66cc; left: 10%; animation-delay: 0s; }}
    .balloon2 {{ background: #ffcc00; left: 30%; animation-delay: 2s; }}
    .balloon3 {{ background: #66ccff; left: 50%; animation-delay: 4s; }}
    .balloon4 {{ background: #ff99ff; left: 70%; animation-delay: 1s; }}
    .balloon5 {{ background: #00ff99; left: 90%; animation-delay: 3s; }}

    
    </style>

    <div class="title-wrapper">
      <div class="title-box box1">
        Welcome ! {username}  💐 🎉
      </div>
      <div class="title-box box2">
         Access Granted  👍🤝  
      </div>
    </div>

    <div class="balloons">
        <div class="balloon balloon1"></div>
        <div class="balloon balloon2"></div>
        <div class="balloon balloon3"></div>
        <div class="balloon balloon4"></div>
        <div class="balloon balloon5"></div>

        
    </div>
    """, unsafe_allow_html=True)


def display_messages_below_title():
    if st.session_state.get("warning_msg"):
        st.markdown(f"<div class='warning-msg'>{st.session_state['warning_msg']}</div>", unsafe_allow_html=True)
        st.session_state["warning_msg"] = ""
    if st.session_state.get("success_msg"):
        st.markdown(f"<div class='success-msg'>{st.session_state['success_msg']}</div>", unsafe_allow_html=True)
        st.session_state["success_msg"] = ""

def main():
    init_session()
    
    # Set background based on current state
    if st.session_state.get("verified", False):
        set_background(success_bg)
    elif st.session_state.get("otp_sent", False):
        set_background(otp_bg)
    else:
        set_background(login_bg)

    # Auto-refresh logic
    auto_refresh_needed = (
        st.session_state["otp_sent"]
        and not st.session_state["verified"]
        and not st.session_state["timer_expired"]
    )
    if auto_refresh_needed:
        st_autorefresh(interval=1000, limit=None, key="timer_refresh")

    # If OTP has been sent, wrap content in OTP page wrapper
    if st.session_state.get("otp_sent", False):
        st.markdown('<div class="otp-page">', unsafe_allow_html=True)
    
    # Main layout columns
    left_space, content, right_space = st.columns([0.5, 6.5, 0.5])
    with content:
        col1, col2 = st.columns([4, 3.5], gap="small")
        with col1:
            st.write("")
        with col2:
            if st.session_state["verified"]:
                final_success_screen()
                display_messages_below_title()
            elif st.session_state["otp_sent"]:
                render_otp_screen()
            else:
                st.markdown("""
                <style>
                .login-title-container {
                    float: none !important;
                    width: 310px !important; 
                    text-align: left !important;
                    padding: 10px;
                    border-radius: 14px;
                    box-shadow: 0px 6px 14px rgba(0, 0, 0, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.5);
                    margin-bottom: 35px !important;
                    margin-top: 35px !important;
                    height: 70px !important;
                }
                .login-title {
                    color: #ffffff !important;
                    font-size: 25px;
                    font-weight: 600;
                    letter-spacing: 1px;
                    text-shadow: 1px 1px 6px rgba(255, 255, 255, 0.5);
                    margin: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                }
                .login-icon {
                    width: 40px;  
                    height: 40px;
                }
                </style>
                <div class="login-title-container">
                    <div class="login-title">
                        <svg class="login-icon" viewBox="0 0 24 24" fill="black" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="12" cy="7" r="4"></circle>
                            <path d="M12 14c-5.33 0-8 2.67-8 4v2h16v-2c0-1.33-2.67-4-8-4z"></path>
                        </svg>
                        USER LOGIN PAGE
                    </div>
                </div>
                """, unsafe_allow_html=True)
                render_login_form()
                display_messages_below_title()
    
    if st.session_state.get("otp_sent", False):
        st.markdown('</div>', unsafe_allow_html=True)

    

if __name__ == "__main__":
    main()
