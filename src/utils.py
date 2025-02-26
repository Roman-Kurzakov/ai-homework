import re
import html
import logging
import requests
import base64
import os
import uuid
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def markdown_to_html(text):
    logging.debug("Исходный текст: %s", text)

    # Шаг 1: Заменяем блоки кода на уникальные маркеры
    code_blocks = {}

    def replace_code_block(match):
        code_content = match.group(1)
        placeholder = f"«CODE_BLOCK_{len(code_blocks)}»"
        code_blocks[placeholder] = code_content
        logging.debug("Найден блок кода: %s", code_content)
        return placeholder

    text = re.sub(r'```(.*?)```', replace_code_block, text, flags=re.DOTALL)
    logging.debug("Текст после замены блоков кода: %s", text)

    # Шаг 2: Заменяем инлайн-код на уникальные маркеры
    inline_codes = {}

    def replace_inline_code(match):
        code_content = match.group(1)
        placeholder = f"«INLINE_CODE_{len(inline_codes)}»"
        inline_codes[placeholder] = code_content
        logging.debug("Найден инлайн-код: %s", code_content)
        return placeholder

    text = re.sub(r'`(.*?)`', replace_inline_code, text)
    logging.debug("Текст после замены инлайн-кода: %s", text)

    # Шаг 2.1: Обрабатываем LaTeX-формулы как инлайн-код
    def replace_latex(match):
        code_content = match.group(1)
        placeholder = f"«INLINE_CODE_{len(inline_codes)}»"
        inline_codes[placeholder] = code_content
        logging.debug("Найдена LaTeX-формула: %s", code_content)
        return placeholder

    # Обрабатываем инлайн-формулы \( ... \)
    text = re.sub(r'\\\((.*?)\\\)', replace_latex, text, flags=re.DOTALL)
    # Обрабатываем блочные формулы \[ ... \]
    text = re.sub(r'\\\[(.*?)\\\]', replace_latex, text, flags=re.DOTALL)

    # Шаг 3: Обрабатываем Markdown-разметку
    # Жирный текст '**текст**' -> '<b>\1</b>'
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Курсив '*текст*' -> '<i>\1</i>'
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Зачёркнутый текст '~~текст~~' -> '<s>\1</s>'
    text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)
    # Подчёркнутый текст '__текст__' -> '<u>\1</u>'
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
    # Ссылки '[текст](URL)' -> '<a href="\2">\1</a>'
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
    logging.debug("Текст после обработки Markdown-разметки: %s", text)

    # Шаг 4: Восстанавливаем инлайн-код и LaTeX-формулы
    def restore_inline_code(match):
        placeholder = match.group(0)
        code_content = inline_codes.get(placeholder, "")

        # Шаг 1: Удаление \text{...} => ...
        code_content = re.sub(r'\\text\{(.*?)\}', r'\1', code_content)
        # Шаг 2: Обработка \frac{...}{...} => .../...
        #code_content = re.sub(r'\\frac\{(.*?)\}\{(.*?)\}', r'\1/\2', code_content)
        code_content = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1 / \2', code_content)

        # Шаг 3: Замена LaTeX-команд на соответствующие символы
        replacements = {
            # Операторы и стрелки
            r'\\times': '*',
            r'\\rightarrow': '→',
            r'\\leftarrow': '←',
            r'\\leftrightarrow': '↔',
            r'\\leftrightharpoons': '⇋',
            r'\\rightleftharpoons': '⇌',
            r'\\Rightarrow': '⇒',
            r'\\Leftarrow': '⇐',
            r'\\Leftrightarrow': '⇔',
            r'\\longrightarrow': '⟶',
            r'\\longleftarrow': '⟵',
            r'\\longleftrightarrow': '⟷',
            r'\\uparrow': '↑',
            r'\\downarrow': '↓',

            # Математические символы
            r'\\pm': '±',
            r'\\neq': '≠',
            r'\\leq': '≤',
            r'\\geq': '≥',
            r'\\approx': '≈',
            r'\\equiv': '≡',
            r'\\infty': '∞',
            r'\\cdot': '·',
            r'\\sqrt': '√',
            r'\\int': '∫',
            r'\\sum': '∑',
            r'\\prod': '∏',
            r'\\lim': 'lim',
            r'\\to': '→',
            r'\\d': 'd',
            r'\\partial': '∂',

            # Греческие буквы
            r'\\Delta': 'Δ',
            r'\\delta': 'δ',
            r'\\alpha': 'α',
            r'\\beta': 'β',
            r'\\gamma': 'γ',
            r'\\Gamma': 'Γ',
            r'\\pi': 'π',
            r'\\Pi': 'Π',
            r'\\omega': 'ω',
            r'\\Omega': 'Ω',
            r'\\theta': 'θ',
            r'\\Theta': 'Θ',
            r'\\phi': 'φ',
            r'\\Phi': 'Φ',
            r'\\psi': 'ψ',
            r'\\Psi': 'Ψ',
            r'\\sigma': 'σ',
            r'\\Sigma': 'Σ',
            r'\\epsilon': 'ε',
            r'\\varepsilon': 'ε',
            r'\\rho': 'ρ',
            r'\\lambda': 'λ',
            r'\\Lambda': 'Λ',
            r'\\eta': 'η',
            r'\\zeta': 'ζ',
            r'\\Zeta': 'Ζ',
            r'\\xi': 'ξ',
            r'\\Xi': 'Ξ',
            r'\\nu': 'ν',
            r'\\Nu': 'Ν',
            r'\\mu': 'μ',
            r'\\Mu': 'Μ',
            r'\\chi': 'χ',

            # Скобки
            r'\\langle': '⟨',
            r'\\rangle': '⟩',
            r'\\lceil': '⌈',
            r'\\rceil': '⌉',
            r'\\lfloor': '⌊',
            r'\\rfloor': '⌋',

            # Индексы и степени
            r'\^': '^',
            r'\_': '_',
            r'\\lim_{': 'lim_',
            r'\\int_{': '∫_',
            r'\\sum_{': '∑_',

            # Прочие математические символы
            r'\\propto': '∝',
            r'\\subset': '⊂',
            r'\\supset': '⊃',
            r'\\subseteq': '⊆',
            r'\\supseteq': '⊇',
            r'\\notin': '∉',
            r'\\in': '∈',
            r'\\cup': '∪',
            r'\\cap': '∩',
            r'\\forall': '∀',
            r'\\exists': '∃',
            r'\\nabla': '∇',

            # Дополнительные
            r'\\angle': '∠',
            r'\\perp': '⊥',
            r'\\parallel': '∥',
            r'\\,': ' ',
            r'###': ' '
        }

        for pattern, replacement in replacements.items():
            code_content = re.sub(pattern, replacement, code_content)

        # Шаг 4: Обработка верхних индексов
        def replace_superscripts(content):
            superscript_map = str.maketrans('0123456789+-=()n', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ')
            return content.translate(superscript_map)

        code_content = re.sub(r'\^(\{([^{}]+?)\}|(\S))', lambda m: replace_superscripts(m.group(2) or m.group(3)), code_content)

        # Шаг 5: Обработка нижних индексов
        def replace_subscripts(content):
            subscript_map = str.maketrans('0123456789+-=()aehklmnoprstuvx', '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕₖₗₘₙₒₚᵣₛₜᵤᵥₓ')
            return content.translate(subscript_map)

        code_content = re.sub(r'_(\{([^{}]+?)\}|(\S))', lambda m: replace_subscripts(m.group(2) or m.group(3)), code_content)

        # Шаг 6: Экранирование HTML-сущностей
        code_content = html.escape(code_content)

        logging.debug("Восстановленный инлайн-код: %s", code_content)
        return f'<code>{code_content}</code>'

    text = re.sub(r'«INLINE_CODE_\d+»', restore_inline_code, text)
    logging.debug("Текст после восстановления инлайн-кода: %s", text)

    # Шаг 5: Восстанавливаем блоки кода
    def restore_code_block(match):
        placeholder = match.group(0)
        code_content = code_blocks.get(placeholder, "")
        code_content = html.escape(code_content)
        logging.debug("Восстановленный блок кода: %s", code_content)
        return f'<pre><code>{code_content}</code></pre>'

    text = re.sub(r'«CODE_BLOCK_\d+»', restore_code_block, text, flags=re.DOTALL)
    logging.debug("Текст после восстановления блоков кода: %s", text)

    return text


load_dotenv()

# Данные ЮKassa
SHOP_ID = os.getenv("SHOP_ID")
SECRET_KEY = os.getenv("U_KASSA_KEY")


# Функция для создания платёжной ссылки
def create_payment(amount, description, user_id, tariff_name):
    url = "https://api.yookassa.ru/v3/payments"
    auth = base64.b64encode(f"{SHOP_ID}:{SECRET_KEY}".encode()).decode()

    payment_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Idempotence-Key": payment_id
    }

    data = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/HomeworkSolvBot"
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": str(user_id),
            "tariff_name": tariff_name
        }
    }

    response = requests.post(url, json=data, headers=headers)
    logging.info(f"Ответ ЮKassa: {response.status_code}, {response.text}")
    if response.status_code == 200 or response.status_code == 201:
        return response.json()["confirmation"]["confirmation_url"]
    else:
        logging.error(f"Ошибка при создании платежа: {response.text}")
        return None
