import time
from openai import OpenAI
from tempfile import NamedTemporaryFile
import os
import re
from instance.config import Config 

client = OpenAI(
    api_key=Config.OPEN_AI_API_KEY,
)

def transcribe_audio(audio_file):
    with NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        audio_file.save(tmp.name)
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp.name, "rb")
            )
            return transcription.text
         
        finally:
            os.unlink(tmp.name)

def abstract_summary_extraction(transcription):
    response = client.chat.completions.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response.choices[0].message.content

def key_points_extraction(transcription):
    response = client.chat.completions.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a proficient AI with a specialty in distilling information into key points. Based on the following text, identify and list the main points that were discussed or brought up. These should be the most important ideas, findings, or topics that are crucial to the essence of the discussion. Your goal is to provide a list that someone could read to quickly understand what was talked about."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response.choices[0].message.content

def action_item_extraction(transcription):
    response = client.chat.completions.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an AI expert in analyzing conversations and extracting action items. Please review the text and identify any tasks, assignments, or actions that were agreed upon or mentioned as needing to be done. These could be tasks assigned to specific individuals, or general actions that the group has decided to take. Please list these action items clearly and concisely."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response.choices[0].message.content

def sentiment_analysis(transcription):
    response = client.chat.completions.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "As an AI with expertise in language and emotion analysis, your task is to analyze the sentiment of the following text. Please consider the overall tone of the discussion, the emotion conveyed by the language used, and the context in which words and phrases are used. Indicate whether the sentiment is generally positive, negative, or neutral, and provide brief explanations for your analysis where possible."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response.choices[0].message.content

def clean_title(title):
    cleaned_title = re.sub(r"\s+", "_", title)
    cleaned_title = re.sub(r"[^a-zA-Z0-9\-_.]", "", cleaned_title)
    cleaned_title = re.sub(r"__+", "_", cleaned_title)
    
    return cleaned_title

def title(transcription):
    response = client.chat.completions.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role":"system",
                "content":"You are a proficient AI with a specialty in distilling information into key points. Based on the following text, creates a title that will be used to name a file."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response.choices[0].message.content

def meeting_minutes(transcription):
    abstract_summary = abstract_summary_extraction(transcription)
    key_points = key_points_extraction(transcription)
    action_items = action_item_extraction(transcription)
    sentiment = sentiment_analysis(transcription)
    return {
        'abstract_summary': abstract_summary,
        'key_points': key_points,
        'action_items': action_items,
        'sentiment': sentiment
    }

def dict_to_html(dicionario, download_url):
    html_output = ""
    for key, value in dicionario.items():
        title = ' '.join(word.capitalize() for word in key.split('_'))
        html_output += f"<h3>{title}</h3>\n<p>{value}</p>\n"
    # Adicionar o botão de download
    html_output += f'''
    <a href="{download_url}" class="btn btn-primary btn-download">
        Baixar Relatório 
        <svg class="download-symbol" width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 17H17.01M17.4 14H18C18.9319 14 19.3978 14 19.7654 14.1522C20.2554 14.3552 20.6448 14.7446 20.8478 15.2346C21 15.6022 21 16.0681 21 17C21 17.9319 21 18.3978 20.8478 18.7654C20.6448 19.2554 20.2554 19.6448 19.7654 19.8478C19.3978 20 18.9319 20 18 20H6C5.06812 20 4.60218 20 4.23463 19.8478C3.74458 19.6448 3.35523 19.2554 3.15224 18.7654C3 18.3978 3 17.9319 3 17C3 16.0681 3 15.6022 3.15224 15.2346C3.35523 14.7446 3.74458 14.3552 4.23463 14.1522C4.60218 14 5.06812 14 6 14H6.6M12 15V4M12 15L9 12M12 15L15 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </a>
    <a href="#" class="btn btn-success btn-save">
        Salvar 
        <svg class="save-symbol" width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H14L19 8V19C19 20.1046 18.1046 21 17 21Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 17V11" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 14H15" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </a>
    <a href="/new_report" class="btn btn-danger btn-new">
        Novo 
        <svg class="new-symbol" width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5V19" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5 12H19" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </a>
    '''

    return html_output

def report_generator(audio_file):
    try:
        # transcription = transcribe_audio(audio_file)
        # minutes = meeting_minutes(transcription)
        # doc_title = clean_title(title(transcription).replace('"', ""))

        transcription = "Good afternoon, everyone, and welcome to Fintech Plus Sync's 2nd quarter 2023 earnings call. I'm John Doe, CEO of Fintech Plus. We've had a stellar Q2 with a revenue of $125 million, a 25% increase year over year. Our gross profit margin stands at a solid 58%, due in part to cost efficiencies gained from our scalable business model. Our EBITDA has surged to $37.5 million, translating to a remarkable 30% EBITDA margin. Our net income for the quarter rose to $16 million, which is a noteworthy increase from $10 million in Q2 2022. Our total addressable market has grown substantially, thanks to the expansion of our high-yield savings product line and the new RoboAdvisor platform. We've been diversifying our asset-backed securities portfolio, investing heavily in collateralized debt obligations and residential mortgage-backed securities. We've also invested $25 million in AAA-rated corporate bonds, enhancing our risk-adjusted returns. As for our balance sheet, total assets reached $1.5 billion, with total liabilities at $900 million, leaving us with a solid equity base of $600 million. Our debt-to-equity ratio stands at 1.5, a healthy figure considering our expansionary phase. We continue to see substantial organic user growth, with customer acquisition costs dropping by 15% and lifetime value growing by 25%. Our LTVCAC ratio is at an impressive 3.5%. In terms of risk management, we have a value-at-risk model in place, with a 99% confidence level indicating that our maximum loss will not exceed $5 million in the next trading day. We've adopted a conservative approach to managing our leverage, and have a healthy tier-one capital ratio of 12.5%. Our forecast for the coming quarter is positive. We expect revenue to be around $135 million and 8% quarter-over-quarter growth, driven primarily by our cutting-edge blockchain solutions and AI-driven predictive analytics. We're also excited about the upcoming IPO of our fintech subsidiary, Pay Plus, which we expect to raise $200 million, significantly bolstering our liquidity and paving the way for aggressive growth strategies. We thank our shareholders for their continued faith in us, and we look forward to an even more successful Q3. Thank you so much."
        minutes = {'abstract_summary': "Fintech Plus Sync reported a 30% EBITDA margin. Net income rose to $16 million, up from $10 million in Q2 2022. The company's total addressable market expanded due to the growth of its high-yield savings product line and the new RoboAdvisor platform. Fintech Plus Sync diversified its asset-backed securities portfolio and invested $25 million in AAA-rated corporate bonds. The company's total assets reached $1.5 billion, with total liabilities at $900 million, resulting in a solid equity base of $600 million. The company also reported substantial organic user growth, with a decrease in customer acquisition costs and an increase in lifetime value. The company's forecast for the next quarter is positive, expecting revenue of around $135 million and 8% QoQ growth. The upcoming IPO of its fintech subsidiary, Pay Plus, is expected to raise $200 million, bolstering liquidity and enabling aggressive growth strategies.\n", 'key_points': "1. Fintech Plus Sync reported a successful Q2 2023 with a revenue of $125 million, a 25% increase year over year.\n2. The company's gross profit margin stands at 58%, attributed to cost efficiencies from their scalable business model.\n3. The EBITDA surged to $37.5 million, translating to a 30% EBITDA margin.\n4. Net income for the quarter rose to $16 million, a significant increase from $10 million in Q2 2022.\n5. The total addressable market has grown due to the expansion of the high-yield savings product line and the new RoboAdvisor platform.\n6. The company diversified its asset-backed securities portfolio, investing heavily in collateralized debt obligations and residential mortgage-backed securities.\n7. Fintech Plus Sync invested $25 million in AAA-rated corporate bonds to enhance risk-adjusted returns.\n8. The balance sheet shows total assets of $1.5 billion, total liabilities of $900 million, and an equity base of $600 million.\n9. The debt-to-equity ratio stands at 1.5, considered healthy for the company's expansionary phase.\n10. The company reported substantial organic user growth, with customer acquisition costs dropping by 15% and lifetime value growing by 25%.\n11. The company has a value-at-risk model in place, indicating a maximum loss of $5 million in the next trading day at a 99% confidence level.\n12. The company maintains a healthy tier-one capital ratio of 12.5%.\n13. The forecast for the next quarter is positive, with expected revenue of $135 million and 8% quarter-over-quarter growth.\n14. The growth is expected to be driven by blockchain solutions and AI-driven predictive analytics.\n15. The company is preparing for the IPO of its fintech subsidiary, Pay Plus, expected to raise $200 million, which will significantly increase liquidity and support aggressive growth strategies.", 'action_items': "No specific tasks, assignments, or actions were identified in the text. The text is a summary of a company's financial performance and future expectations, but does not include any specific tasks or actions to be taken.", 'sentiment': "The sentiment of the text is overwhelmingly positive. The language used throughout the text conveys a sense of success, growth, and optimism. The CEO of Fintech Plus, John Doe, discusses the company's impressive financial performance in Q2 2023, highlighting a 25% increase in revenue, a solid gross profit margin, and a significant increase in net income. He also mentions the company's successful diversification strategies, healthy balance sheet, and effective risk management. The forecast for the next quarter is also positive, with expected revenue growth and the upcoming IPO of a subsidiary. The closing thanks to shareholders for their continued faith further reinforces the positive sentiment."}
        doc_title = clean_title("Fintech Plus Sync's Q2 2023 Earnings")
        message = {"status":"done","message":""}

        time.sleep(3)

        return minutes, doc_title, message

    except Exception as e:
        message = {"status":"exception","message":e}

        return message