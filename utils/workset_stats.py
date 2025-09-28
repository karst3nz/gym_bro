import statistics
from io import BytesIO
import matplotlib.pyplot as plt
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
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


def make_workset_stats(user_id: int, exercise_name: str, exerise_id: int, period_days: int = 90, show_records: str = "True"):
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

    # Получаем подходы по упражнению
    db.cursor.execute(
        """
        SELECT weight, reps, date FROM records
        WHERE user_id = ? AND exercise = ? AND date >= ?
        ORDER BY date ASC
        """,
        (user_id, exercise_name, start_ts)
    )    
    records = db.cursor.fetchall()
    

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
    def plot_worksets(worksets, exercise_name, records, show_records):
        if not worksets:
            return None

        dates = [datetime.datetime.fromtimestamp(d) for _, _, d in worksets]
        weights = [w for w, _, _ in worksets]
        reps = [r for _, r, _ in worksets]

        # Делаем график больше
        fig, ax1 = plt.subplots(figsize=(9, 4))

        ax1.set_title(f'{exercise_name} — вес, повторения и рекорд', pad=15)
        ax1.set_xlabel('')

        # Вес
        ax1.set_ylabel('Вес (кг)', color='tab:blue')
        ax1.plot(dates, weights, color='tab:blue', marker='o', label='Вес')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        # Повторения
        ax2 = ax1.twinx()
        ax2.set_ylabel('Повторения', color='tab:orange')
        ax2.plot(dates, reps, color='tab:orange', marker='x', linestyle='--', label='Повторы')
        ax2.tick_params(axis='y', labelcolor='tab:orange')

        # Рекорды
        if records and show_records == "True":
            for w, r, d in records:
                rec_date = datetime.datetime.fromtimestamp(d)

                # Вертикальная красная линия
                ax1.axvline(rec_date, color='tab:red', linestyle=':', alpha=0.7)

                # Верх графика (чуть выше)
                ymax = ax1.get_ylim()[1]

                # Подпись рекорда сверху
                ax1.text(
                    rec_date, ymax, f'{w:.1f}',
                    color='red', fontsize=10, fontweight='bold',
                    ha='center', va='bottom',
                    bbox=dict(facecolor='white', edgecolor='none', pad=0)
                )

        ax1.grid(True)

        # Ручная настройка вместо tight_layout
        fig.subplots_adjust(top=0.88, bottom=0.15, left=0.1, right=0.9)

        bio = BytesIO()
        fig.savefig(bio, format='png')
        bio.seek(0)
        plt.close(fig)
        return bio



    plot_img = plot_worksets(worksets[-200:], exercise_name, records[-200:], show_records) if worksets else None

    # Кнопки смены периода
    def get_button_text(period, current):
        return f'• {period} дн •' if period == current else f'{period} дн'
    def get_records_btn_text(show_record: str):
        return "✅ Показывать рекорд" if show_record == "True" else "❌ Показывать рекорд"
    def get_record_btn(records):
        if records:
            return [InlineKeyboardButton(
                text=get_records_btn_text(show_records),
                callback_data=f"workset_stats:{exerise_id}:{period_days}?{'False' if show_records == 'True' else 'True'}"
            )]
        return None


    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_button_text(7, period_days), callback_data=f"workset_stats:{exerise_id}:7?{show_records}"),
            InlineKeyboardButton(text=get_button_text(30, period_days), callback_data=f"workset_stats:{exerise_id}:30?{show_records}")
        ],
        [
            InlineKeyboardButton(text=get_button_text(90, period_days), callback_data=f"workset_stats:{exerise_id}:90?{show_records}"),
            InlineKeyboardButton(text=get_button_text(365, period_days), callback_data=f"workset_stats:{exerise_id}:365?{show_records}")
        ],
        *([get_record_btn(records)] if get_record_btn(records) else []),
        [
            InlineKeyboardButton(text="⬅️ К выбору упражнений", callback_data="menu:exercises_pages")
        ]
    ])

    text = (
        "<b>📈 Рабочие подходы</b>\n\n"
        f"<b>{exercise_name} ({period_days} дн):</b>\n{stats_text}"
    )

    return text, plot_img, kb
