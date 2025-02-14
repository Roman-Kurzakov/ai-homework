from dotenv import load_dotenv
from enum import Enum
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

RABBIT_LOGIN = os.getenv('RABBIT_LOGIN')
RABBIT_PASS = os.getenv('RABBIT_PASS')
RABBIT_HOST = os.getenv('RABBIT_HOST')
RABBIT_PORT = os.getenv('RABBIT_PORT')

SHOP_ID = os.getenv("SHOP_ID")
SECRET_KEY = os.getenv("U_KASSA_KEY")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ADMIN_ID = int(os.getenv('ADMIN_ID'))

INSTRUCTIONS = {
    'math': "Вставьте сюда инструкцию по математике",
    'russian': "Вставьте сюда инструкцию для русского языка",
    'literature': "Вставьте сюда инструкцию для литературы",
    'english': "Вставьте сюда инструкцию для английского языка",
    'physics': "Вставьте сюда инструкцию для физики",
    'chemistry': "Вставьте сюда инструкцию для химии",
    'biology': "Вставьте сюда инструкцию для биологии",
    'history': "Вставьте сюда инструкцию для истории",
    'social_studies': "Вставьте сюда инструкцию для обществознания",
    'geography': "Вставьте сюда инструкцию для географии",
    'informatics': "Вставьте сюда инструкцию для информатики",
    'other': "Вставьте сюда инструкцию для других предметов"
}


class QueueType(str, Enum):
    AI_REQUEST = "ai_request_queue"


path_to_project = os.path.dirname(os.path.abspath(__file__))
IMAGES_PATH = os.path.join(os.path.dirname(path_to_project), "images")
