from config import *
from database.db import DB
from aiogram import types
from aiogram.fsm.context import FSMContext
from utils.states import States
from utils.menus import start as menu_start
from utils.log import create_logger
import datetime
logger = create_logger(__name__)

db = DB()

@dp.message(States.weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
        if not (20 <= weight <= 400):
            raise ValueError
    except ValueError:
        await message.answer("❗ Введите корректный вес в кг (например: 82.5)")
        return
    now = datetime.datetime.now()
    start_of_day = int(datetime.datetime(now.year, now.month, now.day, 0, 0, 0).timestamp())
    end_of_day = int(datetime.datetime(now.year, now.month, now.day, 23, 59, 59).timestamp())
    db.cursor.execute(
        "SELECT id FROM weights WHERE user_id = ? AND date BETWEEN ? AND ?",
        (message.from_user.id, start_of_day, end_of_day)
    )
    row = db.cursor.fetchone()
    timestamp = int(now.timestamp())
    if row:
        db.cursor.execute(
            "UPDATE weights SET weight = ?, date = ? WHERE id = ?",
            (weight, timestamp, row[0])
        )
        db.conn.commit()
        logger.info(f"Пользователь {message.from_user.id} обновил вес: {weight} кг")
        msg = f"♻️ Вес за сегодня обновлён: {weight} кг"
    else:
        db.cursor.execute(
            "INSERT INTO weights (user_id, weight, date) VALUES (?, ?, ?)",
            (message.from_user.id, weight, timestamp)
        )
        db.conn.commit()
        logger.info(f"Пользователь {message.from_user.id} добавил вес: {weight} кг")
        msg = f"✅ Вес {weight} кг сохранён!"
    await state.clear()
    text, btns = await menu_start(message.from_user.id, state)
    await message.answer(msg, reply_markup=None)
    await message.answer(text, reply_markup=btns)

@dp.message(States.workset)
async def process_workset(message: types.Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) != 3:
        await message.answer("❗ Введите рабочий подход в формате: <b>название, вес, повторения</b>\nНапример: Жим лёжа, 80, 10", parse_mode="HTML")
        return
    exercise, weight, reps = parts
    if not exercise:
        await message.answer("❗ Укажите название упражнения.")
        return
    try:
        weight = float(weight.replace(",", "."))
        reps = int(reps)
        if not (1 <= reps <= 100 and 1 <= weight <= 500):
            raise ValueError
    except ValueError:
        await message.answer("❗ Введите реальные значения веса и повторений.")
        return
    now = datetime.datetime.now()
    start_of_day = int(datetime.datetime(now.year, now.month, now.day, 0, 0, 0).timestamp())
    end_of_day = int(datetime.datetime(now.year, now.month, now.day, 23, 59, 59).timestamp())
    db.cursor.execute(
        "SELECT id FROM worksets WHERE user_id = ? AND exercise = ? AND date BETWEEN ? AND ?",
        (message.from_user.id, exercise, start_of_day, end_of_day)
    )
    row = db.cursor.fetchone()
    timestamp = int(now.timestamp())
    if row:
        db.cursor.execute(
            "UPDATE worksets SET weight = ?, reps = ?, date = ? WHERE id = ?",
            (weight, reps, timestamp, row[0])
        )
        db.conn.commit()
        logger.info(f"Пользователь {message.from_user.id} обновил рабочий подход: {exercise}, {weight} x {reps}")
        msg = f"♻️ Рабочий подход за сегодня обновлён: {exercise}, {weight}кг x {reps}"
    else:
        db.cursor.execute(
            "INSERT INTO worksets (user_id, exercise, weight, reps, date) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, exercise, weight, reps, timestamp)
        )
        db.conn.commit()
        logger.info(f"Пользователь {message.from_user.id} добавил рабочий подход: {exercise}, {weight} x {reps}")
        msg = f"✅ Рабочий подход {exercise}, {weight}кг x {reps} сохранён!"
    await state.clear()
    text, btns = await menu_start(message.from_user.id, state)
    await message.answer(msg, reply_markup=None)
    await message.answer(text, reply_markup=btns)

@dp.message(States.record)
async def process_record(message: types.Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) != 3:
        await message.answer("❗ Введите рекорд в формате: <b>название, вес, повторения</b>\nНапример: Присед, 120, 5", parse_mode="HTML")
        return
    exercise, weight, reps = parts
    if not exercise:
        await message.answer("❗ Укажите название упражнения.")
        return
    try:
        weight = float(weight.replace(",", "."))
        reps = int(reps)
        if not (1 <= reps <= 100 and 1 <= weight <= 700):
            raise ValueError
    except ValueError:
        await message.answer("❗ Введите реальные значения веса и повторений.")
        return
    now = datetime.datetime.now()
    start_of_day = int(datetime.datetime(now.year, now.month, now.day, 0, 0, 0).timestamp())
    end_of_day = int(datetime.datetime(now.year, now.month, now.day, 23, 59, 59).timestamp())
    db.cursor.execute(
        "SELECT id FROM records WHERE user_id = ? AND exercise = ? AND date BETWEEN ? AND ?",
        (message.from_user.id, exercise, start_of_day, end_of_day)
    )
    row = db.cursor.fetchone()
    timestamp = int(now.timestamp())
    if row:
        db.cursor.execute(
            "UPDATE records SET weight = ?, reps = ?, date = ? WHERE id = ?",
            (weight, reps, timestamp, row[0])
        )
        db.conn.commit()
        logger.info(f"Пользователь {message.from_user.id} обновил рекорд: {exercise}, {weight} x {reps}")
        msg = f"♻️ Рекорд за сегодня обновлён: {exercise}, {weight} x {reps}"
    else:
        db.cursor.execute(
            "INSERT INTO records (user_id, exercise, weight, reps, date) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, exercise, weight, reps, timestamp)
        )
        db.conn.commit()
        logger.info(f"Пользователь {message.from_user.id} добавил рекорд: {exercise}, {weight} x {reps}")
        msg = f"✅ Рекорд {exercise}, {weight} x {reps} сохранён!"
    await state.clear()
    text, btns = await menu_start(message.from_user.id, state)
    await message.answer(msg, reply_markup=None)
    await message.answer(text, reply_markup=btns)



