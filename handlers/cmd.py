from datetime import datetime, timedelta
import os
import tempfile

from numpy import average
from config import *
from database.db import DB
from aiogram import types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from utils.log import create_logger
from utils.menus import start as menu_start
import utils.menus as menus
logger = create_logger(__name__)

db = DB()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    db.insert(
        user_id=message.from_user.id,
        tg_username=message.from_user.username or '',
        tg_firstname=message.from_user.full_name or ''
    )
    logger.info(f"Пользователь {message.from_user.id} начал работу с ботом.")
    text, btns = await menu_start(message.from_user.id, state)
    await message.answer(text, reply_markup=btns)


@dp.message(Command("weight"))
async def cmd_weight(msg: types.Message, state: FSMContext):
    text, btns = await menus.weight(msg.from_user.id, state)
    await msg.answer(text, reply_markup=btns)

# @dp.message(Command("record"))
# async def cmd_record(msg: types.Message, state: FSMContext):
#     text, btns = await menus.record(msg.from_user.id, state)
#     await msg.answer(text, reply_markup=btns)

@dp.message(Command("workset"))
async def cmd_workset(msg: types.Message, state: FSMContext):
    text, btns = await menus.workset(msg.from_user.id, state)
    await msg.answer(text, reply_markup=btns)


from utils.weight_stats import make_weight_stats
@dp.message(Command("weight_stats"))
async def cmd_stats(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    text, plot_img, kb = make_weight_stats(user_id, 90)
    if plot_img:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, f"weight_{user_id}.png")
            with open(temp_path, "wb") as f:
                f.write(plot_img.read())
            await message.answer_photo(types.FSInputFile(temp_path), caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


from utils.workset_stats import make_workset_stats, get_common_exercises
@dp.message(Command("workset_stats"))
async def cmd_stats(message: types.Message, state: FSMContext):
    text, btns = await menus.exercises_pages(message.from_user.id, 1)
    await message.answer(text, reply_markup=btns)


@dp.message(Command("test_workset"))
async def test_workset(msg: types.Message):
    db = DB()
    cursor = db.cursor; conn = db.conn

    # Несколько подходов для разных дат — чтобы показать прогресс
    def ts_shift(days: int) -> int:
        """Смещение текущего времени на days (может быть отрицательным)."""
        return int((datetime.now() + timedelta(days=days)).timestamp())

    worksets = [
        # Жим лёжа — постепенный рост веса
        ("Жим лёжа", 70.0, 10, ts_shift(-14)),
        ("Жим лёжа", 75.0, 9, ts_shift(-10)),
        ("Жим лёжа", 80.0, 8, ts_shift(-6)),
        ("Жим лёжа", 85.0, 6, ts_shift(-2)),

        # Приседания со штангой
        ("Приседания со штангой", 100.0, 8, ts_shift(-14)),
        ("Приседания со штангой", 110.0, 6, ts_shift(-10)),
        ("Приседания со штангой", 120.0, 5, ts_shift(-6)),
        ("Приседания со штангой", 130.0, 3, ts_shift(-2)),

        # Становая тяга
        ("Становая тяга", 140.0, 5, ts_shift(-14)),
        ("Становая тяга", 145.0, 4, ts_shift(-10)),
        ("Становая тяга", 150.0, 3, ts_shift(-6)),
        ("Становая тяга", 155.0, 2, ts_shift(-2)),

        # Жим штанги стоя
        ("Жим штанги стоя", 40.0, 12, ts_shift(-14)),
        ("Жим штанги стоя", 45.0, 11, ts_shift(-10)),
        ("Жим штанги стоя", 50.0, 10, ts_shift(-6)),
        ("Жим штанги стоя", 55.0, 8, ts_shift(-2)),
    ]

    cursor.executemany(
        """
        INSERT INTO worksets (user_id, exercise, weight, reps, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(msg.from_user.id, ex, w, r, d) for ex, w, r, d in worksets]
    )
    conn.commit()
    await msg.answer("✅ Тестовые данные добавлены (будет что показать на графиках)")

