import os
import re

import fitz  # PyMuPDF
import requests
import serverless_wsgi
from flask import Flask, jsonify
from flask import request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from textblob import TextBlob

app = Flask(__name__)

SERVICE_ACCOUNT_FILE = os.getenv('SVC_ACCOUNT_FILE', default='teak-trainer-429810-m8-3284cbd4561b.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID', default='1HV_HqjdhP0Qjfdj8LjVCx_Z60pK75aRuJCzhI02FQ6M')


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(stream=pdf_path, filetype="pdf")
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text


def extract_name(text):
    name_pattern = re.compile(r'\b(?:Name:|Candidate:)?\s?([A-Z][a-z]*\s[A-Z][a-z]*)\b|\b([A-Z]+\s[A-Z]+)\b')

    matches = name_pattern.findall(text)
    if matches:
        common_titles = ['Computer Science', 'Quality Assurance', 'Quality Assurance Engineer', 'Summary', 'Education',
                         'Experience', 'Skills']
        for match in matches:
            match = ' '.join(match).strip()
            if match not in common_titles:
                return match
    return "Unknown"


def extract_title(text):
    title_pattern = re.compile(
        r'\b(Software Engineer|Data Scientist|Project Manager|Product Manager|Quality Assurance|Quality Assurance Engineer|Engineer|Software Developer|Front-End Developer|Back-End Developer|Full Stack Developer|DevOps Engineer|Systems Analyst|Business Analyst|Database Administrator|IT Support Specialist|Network Engineer|Cybersecurity Analyst|Machine Learning Engineer|Data Analyst|Data Engineer|UX Designer|UI Designer|Graphic Designer|Marketing Manager|Sales Manager|Account Manager|Financial Analyst|Operations Manager|HR Manager|Content Manager|Digital Marketing Specialist|Technical Writer|Research Scientist|Biomedical Engineer|Mechanical Engineer|Electrical Engineer)\b',
        re.IGNORECASE)
    match = title_pattern.search(text)
    return match.group(0) if match else "Unknown"


def extract_skills(text):
    skill_pattern = re.compile(
        r'\b(Agile|Scrum|Project Management|Data Analysis|Data Science|Machine Learning|Artificial Intelligence|Cloud Computing|AWS|Azure|GCP|DevOps|Docker|Kubernetes|SQL|NoSQL|Java|Python|C\+\+|JavaScript|React|Node\.js|HTML|CSS|TypeScript|Ruby|Ruby on Rails|PHP|Swift|Objective-C|Kotlin|R|Scala|TensorFlow|PyTorch|Hadoop|Spark|Tableau|Power BI|Excel|Word|PowerPoint|Linux|Unix|Windows|Cybersecurity|Penetration Testing|Networking|Customer Service|Sales|Marketing|SEO|Content Creation|Communication|Leadership|Teamwork|Problem-Solving|Time Management|Critical Thinking|Creativity|Adaptability|Attention to Detail|Financial Analysis|Accounting|Budgeting|Forecasting|Healthcare Management|Medical Coding|Patient Care|Clinical Research|Teaching|Curriculum Development|Educational Technology|Legal Research|Contract Management|Litigation|Human Resources|Recruitment|Onboarding|Payroll|Employee Relations|Manufacturing|Lean Manufacturing|Six Sigma|Supply Chain Management|Logistics|Quality Control|Graphic Design|Adobe Photoshop|Adobe Illustrator|CAD|3D Modeling|Public Speaking|Negotiation|Conflict Resolution|Emotional Intelligence|Strategic Planning|Business Development|Product Management|UI/UX Design|Software Development|Systems Engineering|IT Support|Help Desk|Technical Writing|Copywriting|Translation|Bilingual|Multilingual|Event Planning|Hospitality Management|Food Safety|Culinary Arts|Tourism|Real Estate|Property Management|Insurance|Underwriting|Claims Processing|Actuarial Science)\b',
        re.IGNORECASE)
    matches = skill_pattern.findall(text)
    return ', '.join(set(matches)) if matches else "Unknown"


def extract_industries(text):
    industry_keywords = [
        'IT', 'Software Development', 'Software Engineering', 'Software', 'Finance', 'Healthcare',
        'Education', 'Computer Science', 'Web', 'Development', 'Web Development', 'App', 'Engineering',
        'Software Testing', 'Quality', 'Quality Assurance', 'Banking', 'Retail', 'Manufacturing',
        'Telecommunications', 'Energy', 'Transportation', 'Real Estate', 'Legal', 'Entertainment',
        'Media', 'Advertising', 'Aerospace', 'Agriculture', 'Automotive', 'Biotechnology', 'Construction',
        'Consumer Goods', 'E-commerce', 'Government', 'Hospitality', 'Insurance', 'Logistics', 'Mining',
        'Pharmaceuticals', 'Public Sector', 'Publishing', 'Renewable Energy', 'Tourism', 'Utilities'
    ]
    industries = [word for word in industry_keywords if word in text]
    return ', '.join(industries) if industries else "Unknown"


def extract_projects(text):
    project_pattern = re.compile(
        r'(?i)(?:^|\n)'
        r'(?:Projects?|Project Title|Project|❖|•|\*|-|\d+[\.\)]|\bTitle\b|personal projects)\s*'  # Keywords and bullet points
        r'(?:[:\-]\s*)?'
        r'([^\n]+)'
    )

    matches = project_pattern.findall(text)
    matches = [match.strip() for match in matches if match.strip()]
    return ', '.join(set(matches)) if matches else "Unknown"


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
    else:
        text = email_body

    blob = TextBlob(text)
    blob = str(blob)
    candidate_name = extract_name(blob)
    title_position = extract_title(blob)
    skills = extract_skills(blob)
    industries = extract_industries(blob)
    projects_titles = extract_projects(blob)

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

            text = process_resume(response.content)

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


if __name__ == '__main__':
    app.run(debug=True)
