import os
import re
import uuid

import fitz  # PyMuPDF
import requests
import serverless_wsgi
import spacy
from flask import Flask
from flask import request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

nlp = spacy.load('en_core_web_sm')
SERVICE_ACCOUNT_FILE = os.getenv('SVC_ACCOUNT_FILE', default='teak-trainer-429810-m8-e5c5b04a7c29.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

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
    project_titles = []
    title_pattern = re.compile(r'(?i)(?:^|\n)❖\s*(.*?)(?=\n|$)')
    for sent in doc.sents:
        match = title_pattern.search(sent.text)
        if match:
            project_title = match.group(1).strip()
            if project_title:
                project_titles.append(project_title)
    return ', '.join(set(project_titles)) if project_titles else "Unknown"


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
    return result


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        url = data.get('url')

        if url:
            response = requests.get(url)
            response.raise_for_status()

            filename = os.path.basename(url)
            if not filename or filename.find('.') == -1:
                filename = f"{uuid.uuid4()}.pdf"

            if not os.path.exists('downloads'):
                os.makedirs('downloads')

            filepath = os.path.join('downloads', filename)

            with open(filepath, 'wb') as file:
                file.write(response.content)

            text = process_resume(filepath)

            os.remove(filepath)

            return jsonify({'message': 'URL Processed and Google Sheet Updated', 'extracted_text': text}), 200
        else:
            return jsonify({'error': 'Invalid Data'}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return 'Hi'


def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
