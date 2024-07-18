import os
import re

import fitz
import spacy
from flask import Flask, request
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

nlp = spacy.load('en_core_web_sm')
SERVICE_ACCOUNT_FILE = os.getenv('SVC_ACCOUNT_FILE', default='teak-trainer-429810-m8-e5c5b04a7c29.json')
SCOPES = os.getenv('GOOGLE_SCOPES', default='https://www.googleapis.com/auth/spreadsheets')

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID', default='1HV_HqjdhP0Qjfdj8LjVCx_Z60pK75aRuJCzhI02FQ6M')


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text


def extract_name(doc):
    name_pattern = re.compile(r'\b(?:Name:|Candidate:)?\s?([A-Z][a-z]+\s[A-Z][a-z]+)\b')
    matches = name_pattern.findall(doc.text)
    if matches:
        # not match with
        common_titles = ['Computer Science', 'Quality Assurance', 'Quality Assurance Engineer', 'Summary', 'Education',
                         'Experience',
                         'Skills']
        for match in matches:
            if match not in common_titles:
                return match
    return "Unknown"


def extract_title(doc):
    title = None
    for sent in doc.sents:
        if re.search(
                r'\b(Software Engineer|Data Scientist|Project Manager|Product Manager|Quality Assurance|Quality Assurance Engineer|Engineer)\b',
                sent.text,
                re.IGNORECASE):
            title = sent.text
            break
    return title if title else "Unknow"


def extract_skills(doc):
    skills = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and token.dep_ in ["attr", "dobj", "pobj"]:
            skills.append(token.text)
    return ', '.join(set(skills)) if skills else "Unknown"


def extract_industries(doc):
    industry_keywords = ['IT', 'Software Development', 'Software Engineering', 'Software', 'Finance',
                         'Healthcare', 'Education', ' Computer Science', 'Web', 'Development', 'Web Development', 'App',
                         'Engineering', 'Software Testing', 'Quality', 'Quality Assurance']
    industries = [word for word in industry_keywords if word in doc.text]
    return ', '.join(industries) if industries else "Unknown"


def extract_projects(doc):
    projects = []
    project_pattern = re.compile(r'(?i)\b(Project|Title|Summary|Overview):?\s*(.*)')
    for sent in doc.sents:
        match = project_pattern.search(sent.text)
        if match:
            projects.append(match.group(2).strip())
    return ', '.join(set(projects)) if projects else "Unknown"


def append_to_google_sheet(values):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    body = {'values': [values]}
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    return result


def process_resume(pdf_path=None, email_body=None):
    if pdf_path:
        text = extract_text_from_pdf(pdf_path)
        doc = nlp(text)
    else:
        doc = nlp(email_body)
    candidate_name = extract_name(doc)
    title_position = extract_title(doc)
    skills = extract_skills(doc)
    industries = extract_industries(doc)
    projects_titles = extract_projects(doc)

    values = [candidate_name, title_position, skills, industries, projects_titles]
    result = append_to_google_sheet(values)


@app.route('/webhook', methods=['POST'])
def webhook():
    print(f"Received request with content-type: {request.content_type}")
    if request.content_type == 'application/json':
        data = request.json
        resume_content = data.get('resume', '')
        if resume_content:
            process_resume(resume_content)
            return 'Data Processed and Google Sheet Updated'

        email_body = data.get('email_body', '')
        if email_body:
            process_resume(pdf_path=None, email_body=email_body)
            return 'Data Processed and Google Sheet Updated'

        return 'Pdf file or email body not provided'

    return 'Invalid content type, expected application/json'


@app.route('/')
def index():
    return 'Hi'


if __name__ == '__main__':
    app.run(port=5000, debug=True)
