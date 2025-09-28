import statistics
from io import BytesIO
import matplotlib.pyplot as plt
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
import datetime
from database.db import DB

db = DB()

def estimate_1rm(w: float, r: int) -> float:
    if r <= 0:
        return w
    formulas = [
        w / (1 - 0.02 * r),
        w * (1 + 0.0333 * r),
        w * (0.9849 + 0.0328 * r),
        w * 36 / (37 - r),
        w * (1 + r / 30),
        w * (0.988 + 0.0104 * r - 0.00109 * r**2 - 0.0000584 * r**3),
        w * (1.02 ** r),
        w / (1.013 - 0.0267123 * r),
        w * (r ** 0.10),
        w / (0.522 + 0.419 * (2.71828 ** (-0.055 * r))),
        w * 0.951 * (2.71828 ** (0.021 * r)),
        w * (1 + 0.025 * r),
        w / (0.488 + 0.538 * (2.71828 ** (-0.075 * r))),
        w * (1 + r / 30.0),
        w / (1.0278 - 0.0278 * r),
        (100 * w) / (101.3 - 2.67123 * r),
        w * r ** 0.1
    ]

    return float(f"{(sum(formulas) / len(formulas)):.2f}")


def moving_average(values, window=7):
    ma = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        ma.append(sum(values[start:i + 1]) / (i - start + 1))
    return ma

def plot_weight_trend(weights):
    if not weights:
        return None
    dates = [datetime.datetime.fromtimestamp(d) for _, d in weights]
    vals = [w for w, _ in weights]
    plt.figure(figsize=(8, 3))
    plt.plot(dates, vals, marker='o', label='Вес')
    ma = moving_average(vals, window=7)
    if any(ma):
        plt.plot(dates, ma, linestyle='--', label='7-дн. среднее')
    plt.title('Вес — тренд')
    plt.xlabel('')
    plt.grid(True)
    plt.tight_layout()
    plt.legend()
    bio = BytesIO()
    plt.savefig(bio, format='png')
    bio.seek(0)
    plt.close()
    return bio

def make_weight_stats(user_id: int, period_days: int = 90):
    now_ts = int(datetime.datetime.now().timestamp())
    start_ts = now_ts - period_days * 86400
    # ВЕСЫ
    db.cursor.execute("SELECT weight, date FROM weights WHERE user_id = ? AND date >= ? ORDER BY date ASC", (user_id, start_ts))
    weights = db.cursor.fetchall()
    weight_text = "Нет данных."
    if weights:
        first_w, first_d = weights[0]
        last_w, last_d = weights[-1]
        delta = last_w - first_w
        pct = (delta / first_w * 100) if first_w else 0
        avg = statistics.mean([w for w, _ in weights])
        weight_text = (
            f"Последний: <b>{last_w:.1f} кг</b> ({datetime.datetime.fromtimestamp(last_d).strftime('%d.%m.%Y')})\n"
            f"Изменение за {period_days} дн: <b>{delta:+.1f} кг</b> ({pct:+.1f}%)\n"
            f"Средний: {avg:.1f} кг\n"
        )
    # TOP PRs (records)
    db.cursor.execute("SELECT exercise, weight, reps, date FROM records WHERE user_id = ? ORDER BY weight DESC LIMIT 5", (user_id,))
    records = db.cursor.fetchall()
    record_text = "Нет данных."
    if records:
        record_text = "\n".join(
            f"{datetime.datetime.fromtimestamp(d).strftime('%d.%m.%Y')}: <b>{e}</b> — {w} x {r} (1RM ≈ {estimate_1rm(w, r):.0f})"
            for e, w, r, d in records
        )
    # График веса
    plot_img = plot_weight_trend(weights[-200:]) if weights else None
    # Клавиатура — смена периода с выделением текущего
    def get_button_text(period, current_period):
        return f'• {period} дн •' if period == current_period else f'{period} дн'
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_button_text(7, period_days), callback_data="weight_stats:7"), 
         InlineKeyboardButton(text=get_button_text(30, period_days), callback_data="weight_stats:30")],
        [InlineKeyboardButton(text=get_button_text(90, period_days), callback_data="weight_stats:90"), 
         InlineKeyboardButton(text=get_button_text(365, period_days), callback_data="weight_stats:365")],
    ])
    text = (
        "<b>📊 Ваша статистика</b>\n\n"
        f"<b>Вес ({period_days} дн):</b>\n{weight_text}\n\n"
    )
    return text, plot_img, kb