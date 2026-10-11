"""
UPI Safety Coach - Prototype (English only)
-------------------------------------------
A chatbot web app that helps users find out whether a suspicious UPI
situation is a scam, why, and what to do (including what to do if they
have already lost money).

Run:
    pip install streamlit
    streamlit run app.py

SAFETY: this app never asks for a real UPI PIN, OTP, password, card or
account number, and it warns the user if they type something that looks
like one.
"""

import re
import streamlit as st

HELPLINE = "1930"
PORTAL = "cybercrime.gov.in"

# ---------------------------------------------------------------------------
# 1. THE 5 FRAUD SCENARIOS (knowledge base)
# ---------------------------------------------------------------------------
SCENARIOS = {
    "qr": {
        "name": "QR Code Trap",
        "button": "Someone asked me to scan a QR code to get money",
        "keywords": ["qr", "qr code", "scan", "scanner", "receive money",
                     "get money", "barcode"],
        "reason": "Scanning a QR code and entering your PIN always SENDS "
                  "money. You never need to scan anything or enter a PIN "
                  "to RECEIVE money.",
        "red_flags": [
            "\"Scan this QR to receive money / cashback / refund\"",
            "You are asked for your UPI PIN after scanning",
            "Pressure to act quickly",
        ],
        "do_now": [
            "Do NOT scan the code or enter your UPI PIN.",
            "Block and report the sender.",
            "Wait for a normal credit SMS from your bank instead.",
        ],
        "remember": "To receive, never scan.",
        "test": ("A stranger says: 'Scan this QR code to receive your "
                 "Rs 500 cashback.'", "scam",
                 "QR codes are for paying. You never scan to receive money."),
    },
    "otp": {
        "name": "OTP / PIN Theft (Fake Bank or KYC Call)",
        "button": "A 'bank officer' is asking for my OTP / PIN / KYC details",
        "keywords": ["otp", "pin", "upi pin", "kyc", "account blocked",
                     "account will be blocked", "bank officer",
                     "bank manager", "verification code", "verify account",
                     "password", "block", "blocked", "suspended"],
        "reason": "Banks, UPI apps and the police NEVER ask for your OTP or "
                  "UPI PIN. Fraudsters use fear ('account will be blocked') "
                  "and urgency so you act before you think.",
        "red_flags": [
            "Anyone asking for OTP, PIN or password",
            "Urgent deadline: 'update KYC today or account is blocked'",
            "Unknown links or numbers",
        ],
        "do_now": [
            "Hang up or stop replying. Do not share any code.",
            "Call your bank on the number printed on your card or passbook.",
            "Do KYC only in the official bank app or at the branch.",
        ],
        "remember": "OTP is only for you.",
        "test": ("SMS: 'Your account will be blocked today. Click the link "
                 "and share the OTP to update KYC.'", "scam",
                 "Banks never ask for an OTP, and urgent threats are a "
                 "classic scam sign."),
    },
    "screen": {
        "name": "Screen Sharing / Fake Customer Care Scam",
        "button": "Customer care asked me to install an app for a refund",
        "keywords": ["anydesk", "teamviewer", "quicksupport", "remote",
                     "remote access", "screen share", "screen sharing",
                     "customer care", "customer support", "support number",
                     "helpline number", "refund", "install app",
                     "install an app"],
        "reason": "Remote-access apps like AnyDesk or TeamViewer let a "
                  "stranger see and control your phone, including your "
                  "payment apps and OTP messages.",
        "red_flags": [
            "Asked to install AnyDesk, TeamViewer or QuickSupport",
            "Support number found through a random web search",
            "Refund offered but you must 'verify' something first",
        ],
        "do_now": [
            "Do not install the app. If already installed, uninstall it now.",
            "Turn off mobile data / Wi-Fi to cut the connection.",
            "Get customer care numbers only from the official app or website.",
        ],
        "remember": "Your screen. Your control.",
        "test": ("A caller says: 'To process your refund, install AnyDesk "
                 "and tell me the code.'", "scam",
                 "Genuine support never needs remote control of your phone."),
    },
    "olx": {
        "name": "Fake Buyer / Payment Request Scam (OLX type)",
        "button": "A buyer sent me a payment request and says 'accept it'",
        "keywords": ["olx", "buyer", "seller", "accept request",
                     "accept the request", "accept payment",
                     "payment request", "collect request", "request money",
                     "screenshot", "receive payment", "marketplace",
                     "second hand", "rent", "advance"],
        "reason": "Approving a 'collect request' means YOU pay. Scammers "
                  "also send edited payment screenshots to pretend they have "
                  "already paid.",
        "red_flags": [
            "\"Accept the request to receive payment\"",
            "A screenshot is shown instead of a real bank credit message",
            "Buyer is in a hurry or wants to pay extra",
        ],
        "do_now": [
            "Decline the request. Never enter your PIN to receive money.",
            "Confirm payment only from your bank's credit SMS or app.",
            "Hand over the item only after the money is in your account.",
        ],
        "remember": "To get paid, never enter your PIN.",
        "test": ("A buyer says: 'I sent you a request. Accept it and "
                 "enter your PIN so I can pay you.'", "scam",
                 "Receiving money never needs approval or a PIN."),
    },
    "fakeapp": {
        "name": "Fake UPI App / Malicious Link",
        "button": "I got a link to download a new payment app with cashback",
        "keywords": ["apk", "fake app", "download app", "download link",
                     "unofficial", "new app", "payment app", "play store",
                     "app store", "link", "cashback", "reward", "prize",
                     "lucky", "winner", "offer"],
        "reason": "Fake payment apps and links copy real ones to steal your "
                  "login details, PIN and messages. Reward offers are bait "
                  "to make you tap.",
        "red_flags": [
            "App file (APK) or link sent on WhatsApp / SMS",
            "Not available on the official Play Store or App Store",
            "'Claim prize now' or a payment needed to get a reward",
        ],
        "do_now": [
            "Do not open the link or install the file.",
            "Install payment apps only from the official app store.",
            "If installed: uninstall it, change your UPI PIN and passwords, "
            "and call your bank.",
        ],
        "remember": "Think before you tap.",
        "test": ("WhatsApp message: 'Download this APK to get Rs 2,000 "
                 "cashback on UPI payments.'", "scam",
                 "APK files and cashback links from unknown senders are a "
                 "common trap."),
    },
}

# A safe example for the quiz so the user does not think everything is a scam
SAFE_QUIZ_ITEM = (
    "You get a bank SMS: 'Rs 500 credited to your account.' You check the "
    "balance in your official bank app and it matches.", "safe",
    "A credit SMS plus a matching balance in the official app is a normal, "
    "safe transaction.")

QUIZ = [SCENARIOS["qr"]["test"], SAFE_QUIZ_ITEM, SCENARIOS["otp"]["test"],
        SCENARIOS["screen"]["test"], SCENARIOS["olx"]["test"],
        SCENARIOS["fakeapp"]["test"]]

# Triage questions used when the bot cannot match the user's own words
TRIAGE = {
    "They asked for my OTP, PIN or bank details": "otp",
    "They asked me to scan a QR code": "qr",
    "They asked me to install an app (AnyDesk etc.)": "screen",
    "They sent a request to 'accept' to receive money": "olx",
    "They sent a link / app download or a prize offer": "fakeapp",
}
TRIAGE_NONE = "None of these"


# ---------------------------------------------------------------------------
# 2. THE CHATBOT BRAIN
# ---------------------------------------------------------------------------
def kw_hit(keyword, text):
    """Whole-word keyword match (so 'pin' does not match 'shipping')."""
    return re.search(r"\b" + re.escape(keyword) + r"\b", text) is not None


def analyse(text):
    """Return (scenario_id, confidence%) or (None, 0) if nothing matches."""
    text = text.lower()
    scores = {sid: sum(kw_hit(k, text) for k in s["keywords"])
              for sid, s in SCENARIOS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None, 0
    confidence = min(95, 50 + 15 * scores[best])
    return best, confidence


def looks_like_secret(text):
    """Detect something that looks like a PIN / OTP typed into the chat."""
    return re.search(r"\b\d{4,6}\b", text) is not None


def verdict_text(sid, confidence):
    s = SCENARIOS[sid]
    flags = "\n".join(f"- {f}" for f in s["red_flags"])
    steps = "\n".join(f"{i}. {d}" for i, d in enumerate(s["do_now"], 1))
    return (
        f"## 🚨 Verdict: SCAM\n"
        f"**{s['name']}**  \n"
        f"*Match strength: {confidence}%*\n\n"
        f"**Why:** {s['reason']}\n\n"
        f"**Red flags:**\n{flags}\n\n"
        f"**What to do now:**\n{steps}\n\n"
        f"💡 **Remember:** *{s['remember']}*\n\n"
        f"📞 Helpline **{HELPLINE}** | 🌐 **{PORTAL}**"
    )


LOSS_QUESTION = ("One important question: **Have you already sent money, "
                 "shared an OTP/PIN, or installed anything?**")

EMERGENCY_TEXT = (
    "## 🆘 Act fast: the first hour matters\n"
    "1. **Call 1930** (Cyber Crime Helpline) right now and report the "
    "fraud.\n"
    "2. **Call your bank** using the number on your card. Ask them to block "
    "the card/UPI and flag the transaction.\n"
    "3. **Stop all contact** with the scammer. Do not send more money, even "
    "for a 'refund'.\n"
    "4. **Change your UPI PIN and passwords.** Uninstall any app they asked "
    "you to install.\n"
    "5. **Keep proof:** screenshots, phone numbers, transaction ID and time.\n"
    f"6. **File a complaint** at **{PORTAL}** and consider informing your "
    "local police station.\n\n"
    "You are not alone, and being tricked is not your fault. Scammers are "
    "professionals at this."
)

SAFE_TEXT = (
    "## ✅ Good, you stopped in time\n"
    "Your money is safe. To stay protected:\n"
    "1. Never share your UPI PIN or OTP with anyone.\n"
    "2. Verify any unexpected request through the official app or a trusted "
    "contact.\n"
    f"3. Report the sender at **{PORTAL}** to help protect others.\n"
    "4. Share what you learned with family and friends.\n\n"
    "**Stop. Think. Verify. Then pay.**"
)

GENERIC_TEXT = (
    "## 🤔 Verdict: Not sure, so be careful\n"
    "I could not match this to one of my known scams, but that does not "
    "mean it is safe. Please:\n"
    "1. **Pause.** Do not pay, click or share anything yet.\n"
    "2. **Verify** through the official app, website or a number you "
    "already trust.\n"
    "3. **Never share** your OTP or UPI PIN, and never enter a PIN to "
    "receive money.\n"
    f"4. If you feel something is wrong, call **{HELPLINE}**."
)

WELCOME = (
    "👋 Hi! I'm your **UPI Safety Coach**.\n\n"
    "Tell me what happened in your own words, or tap one of the situations "
    "below. I'll tell you if it's a scam, why, and what to do.\n\n"
    "🔒 *Never type your real PIN or OTP here.*  \n"
    "*Educational tool only. Not an official bank, legal or police service.*"
)


def add(role, content):
    st.session_state.messages.append({"role": role, "content": content})


def start_chat():
    st.session_state.messages = []
    st.session_state.stage = "idle"      # idle | triage | ask_loss | done
    st.session_state.current = None
    add("assistant", WELCOME)


def respond_with_verdict(sid, confidence):
    add("assistant", verdict_text(sid, confidence))
    add("assistant", LOSS_QUESTION)
    st.session_state.current = sid
    st.session_state.stage = "ask_loss"


def handle_user(text):
    """Main conversation logic (state machine)."""
    text = text.strip()
    if not text:
        return
    add("user", text)
    stage = st.session_state.stage
    lower = text.lower()

    # Safety guard: never accept real secrets
    if looks_like_secret(text):
        add("assistant",
            "⚠️ **Stop!** That looks like a PIN or OTP. Never type real "
            "codes here, or anywhere except your official payment app. "
            "Please describe the situation in words instead (no numbers).")
        return

    # Stage: asking about loss
    if stage == "ask_loss":
        if lower.startswith("yes"):
            add("assistant", EMERGENCY_TEXT)
            st.session_state.stage = "done"
        elif lower.startswith("no"):
            add("assistant", SAFE_TEXT)
            st.session_state.stage = "done"
        else:
            add("assistant", "Please tap **Yes** or **No** so I can guide "
                             "you correctly.")
        return

    # Stage: triage answer
    if stage == "triage":
        if text in TRIAGE:
            respond_with_verdict(TRIAGE[text], 70)
        else:
            add("assistant", GENERIC_TEXT)
            st.session_state.stage = "done"
        return

    # Button for a known scenario
    for sid, s in SCENARIOS.items():
        if text == s["button"]:
            respond_with_verdict(sid, 90)
            return

    # Free text: greetings / reset
    if lower in ("hi", "hello", "hey", "help", "start", "restart"):
        add("assistant", "Hello! Describe the suspicious message, call or "
                         "request, or pick a situation below.")
        st.session_state.stage = "idle"
        return

    # Free text: analyse
    sid, conf = analyse(text)
    if sid:
        respond_with_verdict(sid, conf)
    else:
        add("assistant",
            "I'm not sure yet. Let me ask: **what did the other person "
            "ask you to do?**")
        st.session_state.stage = "triage"


def click(text):
    """Callback for quick-reply buttons."""
    handle_user(text)


# ---------------------------------------------------------------------------
# 3. QUIZ (Scam or Safe?)
# ---------------------------------------------------------------------------
def start_quiz():
    st.session_state.q_idx = 0
    st.session_state.q_score = 0
    st.session_state.q_feedback = None


def answer_quiz(choice):
    _, truth, why = QUIZ[st.session_state.q_idx]
    if choice == truth:
        st.session_state.q_score += 1
        st.session_state.q_feedback = f"✅ Correct! {why}"
    else:
        st.session_state.q_feedback = f"❌ Not quite. {why}"
    st.session_state.q_idx += 1


# ---------------------------------------------------------------------------
# 4. USER INTERFACE
# ---------------------------------------------------------------------------
st.set_page_config(page_title="UPI Safety Coach", page_icon="🛡️",
                   layout="centered")

if "messages" not in st.session_state:
    start_chat()
if "q_idx" not in st.session_state:
    start_quiz()

with st.sidebar:
    st.header("🛡️ UPI Safety Coach")
    st.markdown(f"**Cyber Crime Helpline:** {HELPLINE}  \n"
                f"**Report online:** {PORTAL}")
    st.markdown("---")
    st.markdown("**Golden rules**\n"
                "- Never share your PIN or OTP\n"
                "- Never scan or enter a PIN to receive money\n"
                "- Never install apps a stranger asks for\n"
                "- Verify before you pay")
    if st.button("🔄 Restart chat"):
        start_chat()
        st.rerun()

st.title("🛡️ UPI Safety Coach")
st.caption("Describe a suspicious situation. I'll tell you if it's a scam "
           "and what to do.")

tab_chat, tab_quiz, tab_lib = st.tabs(
    ["💬 Chatbot", "🎯 Scam or Safe?", "📚 Scam Library"])

# ---- Chat tab -------------------------------------------------------------
with tab_chat:
    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🛡️" if m["role"] ==
                             "assistant" else "🧑"):
            st.markdown(m["content"])

    stage = st.session_state.stage
    n = len(st.session_state.messages)

    if stage == "idle":
        st.write("**Quick replies:**")
        for sid, s in SCENARIOS.items():
            st.button(s["button"], key=f"q_{sid}_{n}", on_click=click,
                      args=(s["button"],), use_container_width=True)
    elif stage == "triage":
        for label in list(TRIAGE) + [TRIAGE_NONE]:
            st.button(label, key=f"t_{label}_{n}", on_click=click,
                      args=(label,), use_container_width=True)
    elif stage == "ask_loss":
        c1, c2 = st.columns(2)
        c1.button("Yes, I already did", key=f"y_{n}", on_click=click,
                  args=("Yes, I already did",), use_container_width=True)
        c2.button("No, I stopped", key=f"n_{n}", on_click=click,
                  args=("No, I stopped",), use_container_width=True)
    elif stage == "done":
        st.button("🔁 Check another situation", key=f"again_{n}",
                  on_click=lambda: setattr(st.session_state, "stage",
                                           "idle"),
                  use_container_width=True)

    user_text = st.chat_input("Describe what happened (no PIN/OTP please)...")
    if user_text:
        handle_user(user_text)
        st.rerun()

# ---- Quiz tab -------------------------------------------------------------
with tab_quiz:
    st.subheader("Think fast: Scam or Safe?")
    idx = st.session_state.q_idx
    if st.session_state.q_feedback:
        st.info(st.session_state.q_feedback)
    if idx < len(QUIZ):
        st.progress(idx / len(QUIZ), text=f"Question {idx + 1} of "
                                          f"{len(QUIZ)}")
        st.markdown(f"> {QUIZ[idx][0]}")
        c1, c2 = st.columns(2)
        c1.button("🚨 Scam", key=f"scam_{idx}", on_click=answer_quiz,
                  args=("scam",), use_container_width=True)
        c2.button("✅ Safe", key=f"safe_{idx}", on_click=answer_quiz,
                  args=("safe",), use_container_width=True)
    else:
        score = st.session_state.q_score
        st.success(f"Your score: {score} / {len(QUIZ)}")
        if score == len(QUIZ):
            st.balloons()
            st.markdown("🏆 **UPI Safety Champion!** Share what you "
                        "learned with your family.")
        elif score >= 4:
            st.markdown("👍 Great job! Review the Scam Library to get "
                        "full marks.")
        else:
            st.markdown("📘 Keep practising: chat with the bot or read "
                        "the Scam Library, then try again.")
        st.button("Play again", on_click=start_quiz)

# ---- Library tab ----------------------------------------------------------
with tab_lib:
    st.subheader("The 5 scams this coach covers")
    for sid, s in SCENARIOS.items():
        with st.expander(s["name"]):
            st.markdown(f"**Why it's a scam:** {s['reason']}")
            st.markdown("**Red flags:**\n" +
                        "\n".join(f"- {f}" for f in s["red_flags"]))
            st.markdown("**What to do:**\n" +
                        "\n".join(f"- {d}" for d in s["do_now"]))
            st.markdown(f"💡 *{s['remember']}*")
