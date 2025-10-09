import secrets
import string
from datetime import datetime
from typing import List
import calendar

from aiogram.types import Chat
from aiogram import Bot
from weasyprint import HTML
import os

def generate_child_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_month_list(year: int = None) -> List[str]:
    """
    Возвращает список месяцев в формате YYYY.MM
    Например: ['2025.12', '2025.11', ..., '2025.01']
    Если year не указан, берется текущий год.
    """
    if year is None:
        year = datetime.now().year
    current_month = 12
    months = [f"{year}.{month:02}" for month in range(current_month, 0, -1)]
    return months


def get_days_from_month_str(month_str: str) -> List[str]:
    """
    Принимает строку 'YYYY.MM' и возвращает список дней месяца в формате 'YYYY.MM.DD'
    """
    year, month = map(int, month_str.split('.'))
    num_days = calendar.monthrange(year, month)[1]
    return [f"{year}.{month:02}.{day:02}" for day in range(1, num_days + 1)]



def format_chat_username(chat: Chat):
    if chat.username:
        return f"@{chat.username}"
    elif chat.full_name:
        return chat.full_name
    else:
        return str(chat.id)


async def resolve_file_paths_aiogram(bot: Bot, reports_data: dict, child_code: str, download_dir="downloads") -> dict:
    os.makedirs(download_dir, exist_ok=True)
    new_data = {}

    for month, exercises in reports_data.items():
        new_data[month] = {}
        for exercise_name, photos in exercises.items():
            new_data[month][exercise_name] = []
            for photo in photos:
                file_id = photo["file_id"]

                file = await bot.get_file(file_id)

                filename = f"{month}_{child_code}_{file_id}.jpg"

                file_path_local = os.path.join(download_dir, filename)
                    
                await bot.download_file(file.file_path, destination=file_path_local)

                new_data[month][exercise_name].append({
                    "file_path": file_path_local,
                    "comments": photo["comments"]
                })

    return new_data


def render_html_to_pdf(html_content: str, output_path: str = "report.pdf"):
    """
    Рендерит HTML в PDF и сохраняет файл
    
    Args:
        html_content (str): HTML-код для рендера
        output_path (str): путь к итоговому PDF
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    HTML(string=html_content, base_url=".").write_pdf(output_path, zoom=0.4)
    print(f"✅ PDF успешно создан: {output_path}")


def html_code_creator(block: str) -> str:
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Журнал прогресса</title>
    <style>
        @page {{
            margin: 0;
            size: A4 landscape;
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            background-color: #f5f7ff;
        }}
        .month-container {{
            display: flex;
            justify-content: flex-end;
            margin-bottom: 10px;
            page-break-inside: avoid;
        }}
        .month {{
            font-weight: bold;
            font-size: 18px;
            text-transform: capitalize;
            color: #ffffff;
            background: linear-gradient(135deg, #4facfe, #2f45f0);
            padding: 4px 10px;
            border-radius: 15px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .month-block {{
            page-break-inside: avoid; /* чтобы месяц и таблица не разрывались */

            transform-origin: top left; /* масштабирование от верхнего левого угла */
        }}
        
        .progress-journal-wrapper {{
            position: relative;
            display: inline-block;
        }}
        
        .progress-journal {{
            border-collapse: collapse;
            background-color: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            margin-bottom: 50px;
            page-break-inside: avoid;
            max-width: 28cm;
        }}
        .progress-journal th,
        .progress-journal td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
            vertical-align: top;
        }}
        .exercise-header {{
            background: linear-gradient(135deg, #2f45f0, #4facfe);
            font-weight: bold;
            text-align: left;
            color: white;
            font-size: 24px;
            padding: 15px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        .exercise-name {{
            font-weight: bold;
            height: 40px; 
            text-align: center;
            vertical-align: middle;
            width: 15%;
            background-color: #2f45f0;
            color: white;
            font-size: 18px;
            padding: 6px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        .exercise-name-inner {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            text-align: center;
            flex-direction: column;
        }}
        .comment-row td {{
            background-color: #6071f4;
            text-align: left;
            font-style: italic;
            color: white;
            font-size: 14px;
            padding: 5px 10px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.4);
        }}
        .exercise-details img {{
            width: 320px;
            height: 240px;
            object-fit: cover;
            display: block;
            margin: 0 auto;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
    </style>
    </head>
    <body>
        {block}
    </body>
    </html>
    """
    return html
