import tempfile
from aiogram import types
from aiogram.fsm.context import FSMContext
from utils.states import States

async def start(user_id: int, state: FSMContext):
    await state.clear()
    text = (
        "👋 <b>Добро пожаловать в GymBro!</b>\n\n"
        "Я помогу вести учёт массы тела и тренировочный дневник.\n\n"
        "Доступные команды:\n"
        "<b>/weight</b> — ввести текущий вес\n"
        "<b>/workset</b> — добавить рабочий подход\n"
        "<b>/record</b> — добавить рекорд\n"
        "<b>/weight_stats</b> — посмотреть статистику по весу тела\n"
        "<b>/workset_stats</b> — посмотреть статистику по рабочим подходам\n"
    )
    btns = types.InlineKeyboardMarkup(
        inline_keyboard=[
            # [types.InlineKeyboardButton(text="Ввести вес", callback_data="menu:weight")],
            # [types.InlineKeyboardButton(text="Рабочий подход", callback_data="menu:workset")],
            # [types.InlineKeyboardButton(text="Рекорд", callback_data="menu:record")],
        ]
    )
    return text, btns


async def weight(user_id: int, state: FSMContext):
    await state.clear()
    await state.set_state(States.weight)
    text = "Введите ваш текущий вес (в кг):"
    btns = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="menu:start")],
        ]
    )
    return text, btns

from utils.workset_stats import get_common_exercises
async def workset(user_id: int, state: FSMContext):
    await state.clear()
    await state.set_state(States.workset)
    text = (
        "Введите рабочий подход в формате: <b>название, вес, повторения</b>\n"
        "Например: <b>Жим лёжа, 80, 10</b>"
    )
    exercises = get_common_exercises(user_id, html=True); exercises = '\n'.join(exercises)
    if len(exercises) >= 1:
        text += (
        "\n\nНазвания ваших упражнений:\n"
        f"{exercises}\n"
        "(Нажмите на название, чтобы скопировать)"
        )
    btns = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="menu:start")],
        ]
    )
    return text, btns

async def record(user_id: int, state: FSMContext):
    await state.clear()
    await state.set_state(States.record)
    text = (
        "Введите рекорд в формате: <b>название, вес, повторения</b>\n"
        "Например: Присед, 120, 5"
    )
    exercises = get_common_exercises(user_id, html=True); exercises = '\n'.join(exercises)
    if len(exercises) >= 1:
        text += (
        "\n\nНазвания ваших упражнений:\n"
        f"{exercises}\n"
        "(Нажмите на название, чтобы скопировать)"
        )
    btns = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="◀️ Назад", callback_data="menu:start")],
        ]
    )
    return text, btns


def gen_exercises_pages(exercises: list, per_page: int = 5):
    """
    Возвращает кортеж:
    - pages: словарь {номер_страницы: [названия упражнений]}
    - id_map: словарь {глобальный_id: название упражнения}
    """
    pages = {}
    id_map = {}
    page_num = 1
    page_context = []
    global_idx = 0

    for exercise in exercises:
        page_context.append(exercise)
        id_map[exercise] = global_idx
        global_idx += 1

        if len(page_context) == per_page:
            pages[page_num] = page_context
            page_context = []
            page_num += 1

    # остаток
    if page_context:
        pages[page_num] = page_context

    return pages, id_map



async def exercises_pages(user_id: int, page: int = 1):
    text = "Выберите упражнение:"
    pages, ids = gen_exercises_pages(get_common_exercises(user_id))
    btns = []
    if len(pages) == 0: return "У вас не записаны рабочие подходы!\n/workset - для записи рабочих подходов", types.InlineKeyboardMarkup(inline_keyboard=[[]])
    for exercise in pages[page]:
        idx = ids.get(exercise)
        btns += [[types.InlineKeyboardButton(text=exercise, callback_data=f"workset_stats:{idx}:90")]]
    if page == 1 and len(pages.keys()) != 1:
        nav_btns = [
            [
                types.InlineKeyboardButton(text=f"{page}/{len(pages.keys())}", callback_data="pass"),
                types.InlineKeyboardButton(text="➡️", callback_data=f"menu:exercises_pages?({page + 1})")
            ]
        ]
    
    elif len(pages.keys()) == 1:
        nav_btns = [[]]        
    
    elif page == len(pages.keys()):
        nav_btns = [
            [
                types.InlineKeyboardButton(text="⬅️", callback_data=f"menu:exercises_pages?({page - 1})"),
                types.InlineKeyboardButton(text=f"{page}/{len(pages.keys())}", callback_data="pass")
            ]
        ]               
    else:
        nav_btns = [
            [
                types.InlineKeyboardButton(text="⬅️", callback_data=f"menu:exercises_pages?({page - 1})"),
                types.InlineKeyboardButton(text=f"{page}/{len(pages.keys())}", callback_data="pass"),
                types.InlineKeyboardButton(text="➡️", callback_data=f"menu:exercises_pages?({page + 1})")
            ]
        ]    
    btns += nav_btns
    return text, types.InlineKeyboardMarkup(inline_keyboard=btns)