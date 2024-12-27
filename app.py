import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
import openai
import os
from dotenv import load_dotenv
from twilio.rest import Client
import time

# ----------------------
# Load Environment Variables
# ----------------------
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
openai.api_key = os.getenv("OPENAI_API_KEY")
PDF_PATH = os.getenv("PDF_PATH")
WEBSITE_URL = os.getenv("WEBSITE_URL")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN =  os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER= os.getenv("TWILIO_WHATSAPP_NUMBER")
USER_WHATSAPP_NUMBER = os.getenv("USER_WHATSAPP_NUMBER")

API_URL_LATEST_MESSAGE = "https://aibytec-bot-4da4777c8a3f.herokuapp.com/api/messages"
API_URL_NEW_MESSAGE = "https://aibytec-bot-4da4777c8a3f.herokuapp.com/api/has_new_messages"

# ----------------------
# Functions
# ----------------------

def Conversation_send(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        client.messages.create(
            body=message,
            from_= TWILIO_WHATSAPP_NUMBER,
            to=USER_WHATSAPP_NUMBER
        )
        st.success("WhatsApp message sent successfully!")
    except Exception as e:
        st.error(f"Error sending WhatsApp message: {e}")

def fetch_latest_message():
    try:
        response = requests.get(API_URL_LATEST_MESSAGE)
        if response.status_code == 200:
            latest_message = response.json()
            return latest_message
        else:
            st.error(f"Error fetching the latest message: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error: {e}")
        return {}

def has_new_message():
    try:
        response = requests.get(API_URL_NEW_MESSAGE)
        if response.status_code == 200:
            return response.json().get("new_message", False)
        else:
            return False
    except Exception as e:
        return False

def send_email(name, email, contact_no, area_of_interest):
    subject = "New User Profile Submission"
    body = f"""
    New Student Profile Submitted:

    Name: {name}
    Email: {email}
    Contact No.: {contact_no}
    Area of Interest: {area_of_interest}
    """
    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = RECEIVER_EMAIL
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        server.quit()
        st.success("Email sent successfully!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

def extract_pdf_text(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def scrape_website(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()
    except Exception as e:
        return f"Error scraping website: {e}"

def chat_with_ai(user_question, website_text, pdf_text, chat_history):
    combined_context = f"Website Content:\n{website_text}\n\nPDF Content:\n{pdf_text}"
    messages = [{"role": "system", "content": "You are a helpful assistant. Use the provided content."}]
    for entry in chat_history:
        messages.append({"role": "user", "content": entry['user']})
        messages.append({"role": "assistant", "content": entry['bot']})
    messages.append({"role": "user", "content": f"{combined_context}\n\nQuestion: {user_question}"})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=256,
            temperature=0.7,
            stream=False
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error generating response: {e}"

# ----------------------
# Streamlit UI and App Logic
# ----------------------

st.set_page_config(page_title="Student Profile & AI Chatbot", layout="wide")

# Session State Initialization
if "page" not in st.session_state:
    st.session_state['page'] = 'form'
if "chat_history" not in st.session_state:
    st.session_state['chat_history'] = []

if st.session_state['page'] == 'form':
    with st.form(key="user_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        contact_no = st.text_input("Contact No.")
        area_of_interest = st.text_input("Area of Interest")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Proceed to Chat")
        with col2:
            continue_chat = st.form_submit_button("Skip and Join Chat")
        
        if submitted:
            if name and email and contact_no and area_of_interest:
                send_email(name, email, contact_no, area_of_interest)
                st.session_state['page'] = 'chat'
                st.rerun()
            else:
                st.warning("Please fill out all fields.")
        
        if continue_chat:
            st.session_state['page'] = 'chat'
            st.rerun()

elif st.session_state['page'] == 'chat':
    # Display chat history
    for entry in st.session_state['chat_history']:
        iconuser = "👤"
        iconbot = "🤖"
        st.markdown(
            f"""
            </div>
            <div style='display: flex; justify-content: right; margin-bottom: 10px;'>
            <div style='display: flex; align-items: center; max-width: 70%; 
                        background-color: #78bae4; color:rgb(255, 255, 255); 
                        padding: 10px; border-radius: 10px;'>
                <span style='margin-right: 10px;'>{iconuser}</span>
                <span>{entry['user']}</span>
            </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            f"""
            </div>
            <div style='display: flex; justify-content: left; margin-bottom: 10px;'>
            <div style='display: flex; align-items: center; max-width: 70%; 
                        background-color: #A9A9A9; color:rgb(255, 255, 255); 
                        padding: 10px; border-radius: 10px;'>
                <span style='margin-right: 10px;'>{iconbot}</span>
                <span>{entry['bot']}</span>
            </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

    # Load PDF and Website content
    pdf_text = extract_pdf_text(PDF_PATH) if os.path.exists(PDF_PATH) else "PDF file not found."
    website_text = scrape_website(WEBSITE_URL)

    user_input = st.chat_input("Type your question here...", key="user_input_fixed")

    if user_input:
        temp = 0
        Conversation_send(user_input)
        time.sleep(2)
        
        with st.spinner("Generating response..."):
            while temp == 0:
                if has_new_message():
                    latest_message = fetch_latest_message()
                    temp = 1
                else:
                    temp = 0
        
        st.session_state['chat_history'].append({"user": user_input, "bot": latest_message["body"]})
        st.rerun()
