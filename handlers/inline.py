import aiogram
from config import *
from utils.log import create_logger
from typing import Callable
from utils.menus import *
import ast
from aiogram import types
from aiogram.fsm.context import FSMContext
from utils.states import States
import tempfile
import os
logger = create_logger(__name__)

@dp.callback_query(F.data == "delete_msg")
async def delete_msg(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.answer()

@dp.callback_query(F.data == "pass")
async def delete_msg(call: types.CallbackQuery, state: FSMContext):
    await call.answer()

from utils.weight_stats import make_weight_stats
@dp.callback_query(lambda c: c.data and c.data.startswith("weight_stats:"))
async def stats_period_cb(call: types.CallbackQuery, state: FSMContext):
    logger.info(
        "Received callback %s from %s",
        call.data,
        (call.from_user.id, call.from_user.full_name)
    )
    period = int(call.data.split(":")[1])
    text, plot_img, kb = make_weight_stats(call.from_user.id, period)
    if plot_img:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, f"weight_{call.from_user.id}.png")
            with open(temp_path, "wb") as f:
                f.write(plot_img.read())
            await call.message.edit_media(
                types.InputMediaPhoto(media=types.FSInputFile(temp_path), caption=text, parse_mode="HTML"),
                reply_markup=kb
            )
    else:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


from utils.workset_stats import make_workset_stats
@dp.callback_query(lambda c: c.data and c.data.startswith("workset_stats:"))
async def stats_period_cb(call: types.CallbackQuery, state: FSMContext):
    logger.info(
        "Received callback %s from %s",
        call.data,
        (call.from_user.id, call.from_user.full_name)
    )
    exercise_id = int(call.data.split(":")[1])
    _, exercises = gen_exercises_pages(get_common_exercises(call.from_user.id));
    for i in exercises.keys():
        key_value = exercises.get(i)
        if exercise_id == key_value: 
            exercise = i
            break
    try: period = int(call.data.split(":")[2].split("?")[0]) 
    except: period = 90
    try: show_records = str(call.data.split("?")[1])
    except Exception as e: show_records = "True"
    text, plot_img, kb = make_workset_stats(call.from_user.id, exercise, exercise_id, period, show_records)
    if plot_img:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, f"workset_{call.from_user.id}.png")
            with open(temp_path, "wb") as f:
                f.write(plot_img.read())
            await call.message.edit_media(
                types.InputMediaPhoto(media=types.FSInputFile(temp_path), caption=text, parse_mode="HTML"),
                reply_markup=kb
            )
    else:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data == F.data)
async def inline_handler(call: types.CallbackQuery, state: FSMContext):
    logger.info(
        "Received callback %s from %s",
        call.data,
        (call.from_user.id, call.from_user.full_name)
    )

    # Работаем только с шаблоном "menu:*"
    if not call.data.startswith("menu:"):
        return

    menu_data = call.data[len("menu:"):]
    if "?" in menu_data:
        menu_name, raw_args = menu_data.split("?", 1)
        # В rare-case, когда строка заканчивается на "?", аргументов нет.
        raw_args = raw_args.strip()
        if raw_args:
            try:
                args = ast.literal_eval(raw_args)
            except (ValueError, SyntaxError):
                logger.warning("Не удалось спарсить аргументы: %s", raw_args)
                args = ()
        else:
            args = ()
    else:
        menu_name, args = menu_data, ()

    # Если parsed object не кортеж — превращаем в кортеж
    if not isinstance(args, tuple):
        args = (args,)

    menu: Callable | None = globals().get(menu_name)
    if menu is None:
        text = "❌ Меню не найдено"
        btns = types.InlineKeyboardMarkup(
            inline_keyboard=[[
                types.InlineKeyboardButton(text="◀️ Назад", callback_data="menu:start")
            ]]
        )
    else:
        # Пробуем разные варианты сигнатур
        try:
            text, btns = await menu(call.message.chat.id, *args, state)
        except Exception as e:
            # logger.error(e)
            try:
                text, btns = await menu(call.message.chat.id, *args)
            except Exception as e:
                # logger.error(e)
                try:
                    text, btns = await menu(*args, state)
                except Exception as e:
                    # logger.error(e)
                    try:
                        text, btns = await menu(call.message.chat.id, state)
                    except Exception as e:
                        logger.error(e)
                        text = f"❌ Не удалось загрузить меню. Ошибка <code>{str(e)}</code>"
                        btns = types.InlineKeyboardMarkup(
                            inline_keyboard=[[
                                types.InlineKeyboardButton(text="◀️ Назад", callback_data="menu:start")
                            ]]
                        )
    try: await call.message.edit_text(
        text=text,
        reply_markup=btns,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    except Exception:
        try:
            await call.message.delete()
            await call.message.answer(
            text=text,
            reply_markup=btns,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        except aiogram.exceptions.TelegramBadRequest:
            await call.answer("ℹ️ Нет изменений...")
        finally:
            await call.answer()
    except aiogram.exceptions.TelegramBadRequest:
        await call.answer("ℹ️ Нет изменений...")
    finally:
        await call.answer()