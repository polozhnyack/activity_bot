import secrets
import string
from datetime import datetime
from typing import List
import calendar

from aiogram.types import Chat
from aiogram import Bot
from weasyprint import HTML
import os
import re

from logger import logger

def generate_child_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def remove_files(data_dict):
    for month, exercises in data_dict.items():
        for exercise_name, items in exercises.items():
            for item in items:
                file_path = item.get("file_path")
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Удалён файл: {file_path}")
                    except Exception as e:
                        logger.error(f"Не удалось удалить {file_path}: {e}")


def delete_file(file_path: str) -> bool:
    """
    Удаляет файл по указанному пути.
    Возвращает True, если файл был удалён, и False, если его не существовало.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Ошибка при удалении файла {file_path}: {e}")
        return False


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


async def resolve_file_paths_aiogram(bot: Bot, child_service, reports_data: dict, child_code: str, download_dir="downloads") -> dict:
    os.makedirs(download_dir, exist_ok=True)
    new_data = {}

    for month, exercises in reports_data.items():
        plans = await child_service.get_monthly_plan(child_id=child_code, month=month)
        if not plans:
            month_plan = "-"
        else:
            month_plan = plans[0].notes if plans[0].notes else "-"

        new_data[month] = {}

        for exercise_name, photos in exercises.items():
            if exercise_name == "Plan":
                continue

            new_data[month][exercise_name] = []
            for photo in photos:
                file_id = photo["file_id"]
                file = await bot.get_file(file_id)
                safe_file_id = re.sub(r'[^a-zA-Z0-9_]', '', file_id)
                filename = f"{month}_{child_code}_{safe_file_id}.jpg"
                file_path_local = os.path.join(download_dir, filename)
                await bot.download_file(file.file_path, destination=file_path_local)

                new_data[month][exercise_name].append({
                    "file_path": file_path_local,
                    "comments": photo["comments"]
                })

        new_data[month]["Plan"] = month_plan

    return new_data



def render_html_to_pdf(html_content: str, output_path: str = "report.pdf"):
    """
    Рендерит HTML в PDF и сохраняет файл
    
    Args:
        html_content (str): HTML-код для рендера
        output_path (str): путь к итоговому PDF
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    HTML(string=html_content, base_url=".").write_pdf(output_path)
    return output_path


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
            size: A3 landscape;
        }}
        html, body {{
            margin: 0;
            padding: 0;
            width: 42cm;
            height: 29.7cm;
            font-family: Arial, sans-serif;
            background-color: #f5f7ff;
        }}
        .progress-journal-wrapper {{
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: flex-start; /* прижать к верху листа */
        }}
        .progress-journal {{
            border-collapse: collapse;
            width: 42cm;
            height: 29.7cm;
            table-layout: fixed;
            background-color: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);

            page-break-inside: auto;
        }}
        .progress-journal th:first-child,
        .progress-journal td:first-child {{
            width: 3.5cm;
            background-color: #2f45f0;
            color: white;
            font-weight: bold;
        }}
        .progress-journal th,
        .progress-journal td {{
            border: 1px solid #ddd;
            text-align: center;
            vertical-align: middle;
            box-sizing: border-box;
            height: calc(29.7cm / 7); /* ровно 7 строк */
            padding: 0;
        }}


        .progress-journal tr {{
            page-break-inside: avoid; /* НЕ разрывать строку */
            page-break-after: auto;    /* Разрыв после строки разрешен */
        }}

        .progress-journal thead {{
            display: table-header-group; /* шапка повторяется на новых страницах */
        }}

        .progress-journal tfoot {{
            display: table-footer-group; /* если нужен футер */
        }}

        .progress-journal th:not(:first-child),
        .progress-journal td:not(:first-child) {{
            width: calc((42cm - 3.5cm) / 12); /* 12 столбцов */
        }}
        .exercise-name-inner {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            text-align: center;
            flex-direction: column;
            font-size: 16px;
            padding: 4px;
        }}
        .exercise-details img {{
            width: 100%;
            height: auto;
            object-fit: cover;
            display: block;
            margin-bottom: 2px;
            border-radius: 6px;
        }}
        .months-row {{
            background: linear-gradient(135deg, #2f45f0, #4facfe);
            color: #fff;
            font-weight: bold;
        }}
        .months-row .month {{
            font-size: 14px;
            padding: 2px;
        }}
        .plan-cell {{
            font-weight: bold;
            color: #2f45f0;
        }}
    </style>
    </head>
    <body>
        <div class="progress-journal-wrapper">
            {block}
        </div>
    </body>
    </html>
    """
    return html




def generate_progress_html_vertical(data: dict, child_name: str = "ФИ ребёнка"):
    months_ru = {
        "01": "январь", "02": "февраль", "03": "март", "04": "апрель",
        "05": "май", "06": "июнь", "07": "июль", "08": "август",
        "09": "сентябрь", "10": "октябрь", "11": "ноябрь", "12": "декабрь"
    }

    html_parts = []
    html_parts.append('<div class="month-block"><div class="progress-journal-wrapper">')
    html_parts.append('<table class="progress-journal">')

    # Заголовок
    html_parts.append(
        f'<tr class="months-row">'
        f'<th class="exercise-name">'
        f'<div class="journal-title">ЖУРНАЛ ПРОГРЕССА</div>'
        f'<div class="child-name">{child_name}</div>'
        f'</th>'
    )

    for i in range(1, 13):
        month_str = f"{i:02d}"
        month_name = months_ru[month_str].capitalize()
        html_parts.append(f'<th class="month">{month_name}</th>')
    html_parts.append('</tr>')

    # Собираем все упражнения, кроме "Plan"
    all_exercises = set()
    for exercises in data.values():
        all_exercises.update(k for k in exercises.keys() if k != "Plan")
    all_exercises = sorted(all_exercises)

    # Рисуем упражнения
    for exercise_name in all_exercises:
        html_parts.append(f'<tr><td class="exercise-name"><div class="exercise-name-inner">{exercise_name}</div></td>')

        for i in range(1, 13):
            month_str = f"{i:02d}"
            matching_key = next((k for k in data.keys() if k.endswith(f"-{month_str}")), None)

            if matching_key:
                exercises = data[matching_key]
                files = exercises.get(exercise_name, [])

                if isinstance(files, list) and files:
                    cell_html = ""
                    for f in files:
                        img_src = f.get("file_path", "")
                        comments = ", ".join(f.get("comments", []))
                        cell_html += (
                            f'<div class="exercise-details">'
                            f'<img src="{img_src}" alt="">'
                            f'<div class="comment-row">{comments}</div>'
                            f'</div>'
                        )
                    html_parts.append(f'<td>{cell_html}</td>')
                else:
                    html_parts.append('<td></td>')
            else:
                html_parts.append('<td></td>')

        html_parts.append('</tr>')

    html_parts.append('<tr><td class="exercise-name"><div class="exercise-name-inner">ОФП</div></td>')
    for i in range(1, 13):
        month_str = f"{i:02d}"
        matching_key = next((k for k in data.keys() if k.endswith(f"-{month_str}")), None)
        if matching_key:
            plan_text = data[matching_key].get("Plan", "")
            html_parts.append(f'<td class="plan-cell">{plan_text}</td>')
        else:
            html_parts.append('<td></td>')
    html_parts.append('</tr>')

    html_parts.append('</table></div></div>')
    return "\n".join(html_parts)
