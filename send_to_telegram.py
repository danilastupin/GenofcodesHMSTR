import os
import requests

api_key = os.getenv('TELEGRAM_API_KEY')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
api_url = f"https://api.telegram.org/bot{api_key}/sendDocument"

folder_path = './downloaded_promo_codes'
for file_name in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file_name)
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as file:
            response = requests.post(api_url, data={'chat_id': chat_id}, files={'document': file})
            response.raise_for_status()
            print(f"{file_name}.")
