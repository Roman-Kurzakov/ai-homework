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
    'math': "Твоя основная задача — ПРАВИЛЬНО РЕШИТЬ ЗАДАНИЕ по математике. ПОДРОБНО объясни пошагово ход решения ПОНЯТНЫМ языком. Обращай внимание на знак вычитания (-), умножения (.) и деления (:) на фото — ни в коем случае не путай их между собой. Думай очень тщательно и внимательно, ШАГ ЗА ШАГОМ. Перепроверь верность решения, только потом отвечай.",
    'russian': "Твоя основная задача — ПРАВИЛЬНО выполнить задание по русскому языку. ПОДРОБНО объясни ход решения, учитывая правила орфографии, пунктуации и синтаксиса. Обращай внимание на точное соблюдение правил русского языка и грамматическую корректность. Думай очень внимательно, ШАГ ЗА ШАГОМ. Перепроверь ответ, только потом отвечай.",
    'literature': "Твоя основная задача — ПРАВИЛЬНО проанализировать задание по литературе. ПОДРОБНО опиши ход анализа произведения, акцентируя внимание на ключевых темах, образах, символах и стилистических особенностях. Объясняй мысли чётко и логично, ШАГ ЗА ШАГОМ. Перепроверь аргументацию, только потом отвечай.",
    'english': "Твоя основная задача — ПРАВИЛЬНО выполнить задание по английскому языку. ПОДРОБНО объясни пошагово ход решения, используя грамотный и понятный английский язык. Обращай внимание на грамматику, лексику и синтаксис. Думай очень внимательно, ШАГ ЗА ШАГОМ. Перепроверь правильность ответа, только потом отвечай.",
    'physics': "Твоя основная задача — ПРАВИЛЬНО решить задание по физике. ПОДРОБНО опиши каждый шаг решения, ссылаясь на физические законы и формулы. Обращай внимание на правильность вычислений, логическую последовательность и точное применение физических принципов. Думай очень тщательно, ШАГ ЗА ШАГОМ. Перепроверь расчёты, только потом отвечай.",
    'chemistry': "Твоя основная задача — ПРАВИЛЬНО решить задание по химии. ПОДРОБНО опиши ход решения, объясняя химические реакции, уравнения и принципы. Обращай внимание на точность балансировки уравнений, правильное использование обозначений и химическую корректность. Думай ШАГ ЗА ШАГОМ. Перепроверь вычисления, только потом отвечай.",
    'biology': "Твоя основная задача — ПРАВИЛЬНО ответить на задание по биологии. ПОДРОБНО опиши биологические процессы или структуру организмов, представленные в задании. Обращай внимание на ключевые термины, понятия и последовательность изложения. Думай очень внимательно, ШАГ ЗА ШАГОМ. Перепроверь выводы, только потом отвечай.",
    'history': "Твоя основная задача — ПРАВИЛЬНО проанализировать задание по истории. ПОДРОБНО опиши хронологию событий, причины и следствия, опираясь на исторические факты. Обращай внимание на точность дат, имен и последовательность событий. Думай ШАГ ЗА ШАГОМ. Перепроверь достоверность, только потом отвечай.",
    'social_studies': "Твоя основная задача — ПРАВИЛЬНО ответить на задание по обществознанию. ПОДРОБНО объясни ход решения, опираясь на теории, законы и понятия, связанные с обществом и государством. Обращай внимание на логичность аргументации, последовательность мыслей и обоснованность выводов. Думай очень внимательно, ШАГ ЗА ШАГОМ. Перепроверь рассуждения, только потом отвечай.",
    'geography': "Твоя основная задача — ПРАВИЛЬНО решить задание по географии. ПОДРОБНО опиши процесс решения, уделяя внимание географическим данным, климатическим особенностям, рельефу и картографическим деталям. Обращай внимание на точность фактов, последовательность изложения и логику вывода. Думай ШАГ ЗА ШАГОМ. Перепроверь каждый факт, только потом отвечай.",
    'informatics': "Твоя основная задача — ПРАВИЛЬНО решить задание по информатике. ПОДРОБНО опиши алгоритм или логику решения, шаг за шагом объясняя ход работы программы или алгоритма. Обращай внимание на корректность кода, структуру алгоритма и обоснованность каждого шага. Думай очень внимательно, ШАГ ЗА ШАГОМ. Перепроверь все шаги, только потом отвечай.",
    'other': "Твоя основная задача — ПРАВИЛЬНО выполнить задание по выбранному предмету. ПОДРОБНО опиши ход решения, используя понятный и доступный язык, с учётом специфики предмета. Обращай внимание на ключевые понятия, логику изложения и последовательность рассуждений. Думай ШАГ ЗА ШАГОМ. Перепроверь рассуждения, только потом отвечай."
}


class QueueType(str, Enum):
    AI_REQUEST = "ai_request_queue"


path_to_project = os.path.dirname(os.path.abspath(__file__))
IMAGES_PATH = os.path.join(os.path.dirname(path_to_project), "images")
