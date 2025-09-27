import re
import statistics
from io import BytesIO
import matplotlib.pyplot as plt
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
import os
import tempfile
import datetime
from database.db import DB
from utils.weight_stats import estimate_1rm, moving_average

db = DB()
cursor = db.cursor; conn = db.conn

def get_common_exercises(user_id: int, html: bool = False):
    raw_worksets = set(cursor.execute("SELECT exercise FROM worksets WHERE user_id = ?", (user_id,)).fetchall())
    worksets = []
    for workset in raw_worksets: 
        if html is False: worksets.append(workset[0])
        else: worksets.append(f"<code>{workset[0]}</code>")
    worksets.sort()
    return worksets


def make_workset_stats(user_id: int, exercise_name: str, exerise_id: int, period_days: int = 90):
    now_ts = int(datetime.datetime.now().timestamp())
    start_ts = now_ts - period_days * 86400

    # Получаем подходы по упражнению
    db.cursor.execute(
        """
        SELECT weight, reps, date FROM worksets
        WHERE user_id = ? AND exercise = ? AND date >= ?
        ORDER BY date ASC
        """,
        (user_id, exercise_name, start_ts)
    )
    worksets = db.cursor.fetchall()

    stats_text = "Нет данных."
    if worksets:
        one_rms = [estimate_1rm(w, r) for w, r, _ in worksets]
        dates = [d for _, _, d in worksets]

        first_w, first_r, first_d = worksets[0]
        last_w, last_r, last_d = worksets[-1]
        first_1rm = estimate_1rm(first_w, first_r)
        last_1rm = estimate_1rm(last_w, last_r)
        delta_1rm = last_1rm - first_1rm
        pct_1rm = (delta_1rm / first_1rm * 100) if first_1rm else 0
        avg_1rm = statistics.mean(one_rms)

        stats_text = (
            f"Последний подход: <b>{last_w:.1f} x {last_r}</b> "
            f"(1RM ≈ {last_1rm}) "
            f"— {datetime.datetime.fromtimestamp(last_d).strftime('%d.%m.%Y')}\n"
            f"Изменение 1RM: <b>{delta_1rm:+.1f}</b> ({pct_1rm:+.1f}%)\n"
            f"Средний 1RM: {avg_1rm:.1f}\n"
        )

    # График
    def plot_worksets(worksets, exercise_name):
        if not worksets:
            return None

        dates = [datetime.datetime.fromtimestamp(d) for _, _, d in worksets]
        weights = [w for w, _, _ in worksets]
        reps = [r for _, r, _ in worksets]

        fig, ax1 = plt.subplots(figsize=(8, 3))

        ax1.set_title(f'{exercise_name} — вес и повторения')
        ax1.set_xlabel('')

        # Вес
        ax1.set_ylabel('Вес (кг)', color='tab:blue')
        ax1.plot(dates, weights, color='tab:blue', marker='o', label='Вес')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        # Повторения (вторичная ось Y)
        ax2 = ax1.twinx()
        ax2.set_ylabel('Повторения', color='tab:orange')
        ax2.plot(dates, reps, color='tab:orange', marker='x', linestyle='--', label='Повторы')
        ax2.tick_params(axis='y', labelcolor='tab:orange')

        fig.tight_layout()
        plt.grid(True)

        bio = BytesIO()
        plt.savefig(bio, format='png')
        bio.seek(0)
        plt.close()
        return bio

    plot_img = plot_worksets(worksets[-200:], exercise_name) if worksets else None

    # Кнопки смены периода
    def get_button_text(period, current):
        return f'• {period} дн •' if period == current else f'{period} дн'
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(7, period_days), callback_data=f"workset_stats:{exerise_id}:7"),
         InlineKeyboardButton(text=get_button_text(30, period_days), callback_data=f"workset_stats:{exerise_id}:30")],
        [InlineKeyboardButton(text=get_button_text(90, period_days), callback_data=f"workset_stats:{exerise_id}:90"),
         InlineKeyboardButton(text=get_button_text(365, period_days), callback_data=f"workset_stats:{exerise_id}:365")],
        [InlineKeyboardButton(text="⬅️ К выбору упражнений", callback_data="menu:exercises_pages")]
    ])

    text = (
        "<b>📈 Рабочие подходы</b>\n\n"
        f"<b>{exercise_name} ({period_days} дн):</b>\n{stats_text}"
    )

    return text, plot_img, kb
