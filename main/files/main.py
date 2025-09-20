import asyncio
import logging
import traceback
import sys
import os
from typing import Optional, Union, Any, Coroutine
import io
import aiogram.exceptions
import yandex_music.exceptions
from setuptools.command.build_py import make_writable
from yandex_music import ClientAsync
import time
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Bot, Dispatcher, types, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from skripts import additionals, admin_commands
from skripts.admin_commands import my_admins_router
from skripts.additionals import Work_with_json as wwjson, Yandex_music_parse as Yparse
from aiogram.fsm.context import FSMContext
from git import Repo
import functools
import coloredlogs

PENDING_REQUESTS = {}
MESSAGE_IDS_ANM_REQUESTS = {}
TOKEN = "7559789537:AAG4vFAdPsTkLNX4EksuT_hIZnK3F4XGD8s"
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()


def get_commands_for_user(user_type):
    match user_type:
        case 'admin':
            _text = ("Команды бота:\n\n/music - предложить музыку\n/profile - Ваш профиль в боте\n/top - топ треков\n/bot_info - тех информация о боте"
                     "\n\nКоманды админа:\n/get_all_users - получить все данные пользователей")
        case 'super_admin':
            _text = ("Команды бота:\n/music - предложить музыку\n/profile - Ваш профиль в боте\n/top - топ треков\n/bot_info - тех информация о боте"
                    "\n\nКоманды админа:\n/get_all_users - получить все данные пользователей"
                     "\n\nКоманды супер-админа:\n/set_recruiting - вкл/выкл набор пользователей\n/add_admin (ID пользователя) - добавить нового админа\n/del_admin (ID пользователя) - удалить админа из состава\n/clear_usersdata - отчистить данные пользователей (классы и треки)")
        case _:
            _text = "Команды бота:\n/music - предложить музыку\n/profile - Ваш профиль в боте\n/top - топ треков\n/bot_info - тех информация о боте"
    return _text



class decorators:

    @staticmethod
    def block_filter() -> any:
        """
        хендлер, проверяющий, не заблокирован ли пользователь
        """
        async def _filter(message: Message) -> Optional[bool]:
            try:
                userdata = wwjson.get_json_data("jsons/Human_souls.json")[str(message.from_user.id)]
            except KeyError:
                return True

            if userdata["soul_name"] != "br0mand":
                if userdata["usertype"] == "blocked":
                    return False
            else:
                return True

        return _filter

    @staticmethod
    def catch_errors(func) -> any:
        """
        Хендлер, который в случае, если в коде при взаимодействии с пользователем происходит ошибка, сообщает об этом
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if str(type(args[0])) == '<class \'aiogram.types.message.Message\'>':
                    userdata = wwjson.get_json_data("jsons/Human_souls.json")[str(args[0].from_user.id)]
                    if userdata["class"] == 0:

                        await start_command(args[0])
                        return None


                return await func(*args, **kwargs)
            except Exception as e:


                tb = sys.exc_info()[2]
                last_trace = traceback.extract_tb(tb)[-1]

                if str(type(e).__name__) == "KeyError":
                    if str(type(args[0])) == '<class \'aiogram.types.message.Message\'>':
                        await start_command(args[0])
                        logging.error(f'{type(e).__name__} on line {last_trace.lineno}: {e}. Отправлено на получение данных')
                    elif str(type(args[0])) == '<class \'aiogram.types.callback_query.CallbackQuery\'>':
                        await args[0].answer()

                        human_souls_data = dict(wwjson.get_json_data("jsons/Human_souls.json"))

                        if str(args[0].from_user.id) not in list(human_souls_data.keys()):
                            human_souls_data[str(args[0].from_user.id)] = {
                                "soul_name": args[0].from_user.username,
                                "usertype": "default",
                                "suggested_music": {},
                                "class": 0,
                                "last_mus": 0
                            }
                            wwjson.send_json_data(human_souls_data, "jsons/Human_souls.json")

                        if human_souls_data[str(args[0].from_user.id)]["class"] == 0:
                            buttons = [
                                [
                                    types.InlineKeyboardButton(text="5", callback_data="set_class_5"),
                                    types.InlineKeyboardButton(text="6", callback_data="set_class_6"),
                                    types.InlineKeyboardButton(text="7", callback_data="set_class_7"),
                                    types.InlineKeyboardButton(text="8", callback_data="set_class_8"),
                                    types.InlineKeyboardButton(text="9", callback_data="set_class_9"),
                                    types.InlineKeyboardButton(text="10", callback_data="set_class_10"),
                                    types.InlineKeyboardButton(text="11", callback_data="set_class_11")
                                ]
                            ]

                            keyboard_pon = types.InlineKeyboardMarkup(inline_keyboard=buttons)

                            await args[0].message.answer("Здравствуйте!\nВыберите ваш класс (это можно сделать единожды):",
                                                 reply_markup=keyboard_pon)

                    return None

                logging.error(f'{type(e).__name__} on line {last_trace.lineno}: {e}')

                code = f'''
                {type(e).__name__} on line {last_trace.lineno}: {e}
                '''
                escaped = code.replace("_", "\\_").replace("*", "\\*") \
                    .replace("[", "\\[").replace("`", "\\`")

                text = f"```python\n{escaped}```"
                if str(type(args[0])) == '<class \'aiogram.types.callback_query.CallbackQuery\'>':
                    await args[0].message.answer((f"❗ Упс! Произошла неизвестная ошибка.\n"
                                          f"Попробуйте выполнить команду /start или проверьте своё интернет‑соединение.\n"
                                          f"Если это не поможет, обратитесь в техническую поддержку: @br0mand\n\n"
                                          f"⚙️ Код ошибки:"))
                    await args[0].message.answer(text, parse_mode="MarkdownV2")
                else:
                    await args[0].answer((f"❗ Упс! Произошла неизвестная ошибка.\n"
                                          f"Попробуйте выполнить команду /start или проверьте своё интернет‑соединение.\n"
                                          f"Если это не поможет, обратитесь в техническую поддержку: @br0mand\n\n"
                                          f"⚙️ Код ошибки:"))
                    await args[0].answer(text, parse_mode="MarkdownV2")


        return wrapper



@dp.message(Command("bot_info"))
@decorators.catch_errors
async def send_info(message: Message) -> None:
    """
    Отправляет пользователю некоторую информацию бота
    Команда: /bot_info
    """
    def count_commits_gitpython(repo_path: str) -> tuple:
        repo = Repo(repo_path)
        commits = list(repo.iter_commits('master'))
        last_commit = repo.head.commit
        return len(commits), last_commit

    vers, last_comit_data = count_commits_gitpython(r"../../")

    start_time = time.perf_counter()
    commit_data = '\n• '.join(str(last_comit_data.message.strip()).split(". "))
    message_before_ping = await message.answer(f'Альфредо 19 \n'
                         f'Версия: V1.{vers}\n'
                         f'---------------------\n'
                         f'Последнее обновление: {last_comit_data.committed_datetime}\n• {commit_data}\n\n'
                         f"Пинг: Загрузка...")
    end_time = time.perf_counter()
    latency = (end_time - start_time) * 1000

    await message_before_ping.edit_text(f'Альфредо 19 \n'
                         f'Версия: V1.{vers}\n'
                         f'---------------------\n'
                         f'Последнее обновление: {last_comit_data.committed_datetime}\n• {commit_data}\n\n'
                         f"Пинг: {latency:.2f} мс")



#Комманда Start
@dp.message(Command("start"))
async def start_command(message: Message) -> None:
    """
    Команда, вызываемая при первом взаимодействии пользователя с ботом.
    Сохраняет его в базу данных и требует некоторую информацию
    """
    human_souls_data = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    if str(message.from_user.id) not in list(human_souls_data.keys()):


        human_souls_data[str(message.from_user.id)] = {
                "soul_name": message.from_user.username,
                "usertype": "default",
                "suggested_music": {},
                "class": 0,
                "last_mus": 0
            }
        wwjson.send_json_data(human_souls_data, "jsons/Human_souls.json")

    if human_souls_data[str(message.from_user.id)]["class"] == 0:
        buttons = [
            [
                types.InlineKeyboardButton(text="5", callback_data="set_class_5"),
                types.InlineKeyboardButton(text="6", callback_data="set_class_6"),
                types.InlineKeyboardButton(text="7", callback_data="set_class_7"),
                types.InlineKeyboardButton(text="8", callback_data="set_class_8"),
                types.InlineKeyboardButton(text="9", callback_data="set_class_9"),
                types.InlineKeyboardButton(text="10", callback_data="set_class_10"),
                types.InlineKeyboardButton(text="11", callback_data="set_class_11")
            ]
        ]

        keyboard_pon = types.InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer("Здравствуйте!\nВыберите ваш класс (это можно сделать единожды):", reply_markup=keyboard_pon)
    else:
        await message.answer(get_commands_for_user(human_souls_data[str(message.from_user.id)]["usertype"]))

@dp.callback_query(lambda c: c.data.startswith("set_class_"))
@decorators.catch_errors
async def set_class_(callback_query: types.CallbackQuery) -> None:
    """
    Устанавливает класс в котором учится пользователь
    """

    class_pon = str(callback_query.data).split("_")[2]
    human_souls_data = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    human_souls_data[str(callback_query.from_user.id)]["class"] = int(class_pon)

    wwjson.send_json_data(human_souls_data, "jsons/Human_souls.json")

    await callback_query.message.answer(get_commands_for_user(human_souls_data[str(callback_query.from_user.id)]["usertype"]))


    await callback_query.answer()
    logging.warning(f"Новый пользователь @{callback_query.from_user.username} из {class_pon} класса!")

class Waiting(StatesGroup):
    waiting_for_music = State()


@dp.message(decorators.block_filter(), Command("music"))
@decorators.catch_errors
async def music(message: Message, state: FSMContext) -> None:
    """
    Запрашивает у пользователя музыку
    Команда: /music
    """
    data = wwjson.get_json_data('./jsons/data.json')

    if not data["recruiting"]:
        await message.answer('❗ В данный момент набор музыки закрыт!')
        return None

    userdata = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    if time.time() - int(userdata[str(message.from_user.id)]["last_mus"]) > 30 or wwjson.is_user_admin(str(message.from_user.id)):
        await message.answer("Введите название вашего трека/треков через запятую:")
        await state.set_state(Waiting.waiting_for_music)
        userdata[str(message.from_user.id)]["last_mus"] = int(time.time())
        wwjson.send_json_data(userdata, "jsons/Human_souls.json")


    else:
        sec = int(userdata[str(message.from_user.id)]["last_mus"])
        await message.answer(f"Вы делаете слишком частые запросы!\nПожалуйста, подождите {30 - (int(time.time()) - int(sec))} сек")


@dp.message(Waiting.waiting_for_music)
@decorators.catch_errors
async def waiting_for_music(message: Message, state: FSMContext) -> None:
    """
    Получает список музыки от пользователя, парсит его и проверяет текст на неприличные выражения.
    В случае, если текст трека не был найден, то отправляет сообщение администраторам, чтобы те его проверили и разрешили/отклонили
    """
    states_pon = []
    musics = message.text.split(",")
    if len(musics) >= 50:
        await message.answer(f"❗ Ошибка, вы предложили слишком много музыки!\n({len(musics)}/50)")
        return None

    query = '\n'.join(states_pon)
    message_query = await message.answer(f"Загрузка...\n<blockquote expandable>{query}</blockquote>")

    for i in musics:
        track_swearing = await yparse.check_text_for_swearing(str(i))
        i = str(i).replace("\n", '')
        if not track_swearing:
            try:
                track = await yparse.parse(i)

            except AttributeError:
                logging.warning(f'⛔ Пользователь @{message.from_user.username} предложил \"{i}\" трек, но трек не был найден!')
                states_pon.append(f"⛔ Трек \"{i}\" не был найден!\n")

            else:

                track_swearing = await yparse.check_text_for_swearing(str(i))
                if not track_swearing:
                    track_swearing = await yparse.check_mus_for_swearing(track)
                    artists = ', '.join([i['name'] for i in track['artists']])

                    visual_name = f'{track["title"]}-{artists}'

                    if track_swearing == "NotFoundError":

                        track_form = wwjson().already_have_that_track(str(track['id']))

                        if track_form == "TrackNotFoundError":
                            logging.warning(f'❔ Пользователь @{message.from_user.username} предложил \"{i}\" трек, но его текст не был найден!')
                            states_pon.append(f"❔ Текст трека \"{i}\" (Распознанный как \"{visual_name}\") не был найден!\n")
                            additionals.suggest_music(None, message.from_user.id, f"{track['id']}", visual_name)
                            asyncio.create_task(send_request_to_admins(message.from_user.username, track, message.from_user.id, i, str(message.from_user.id)))

                        elif not track_form:
                            logging.warning(f'❌ Пользователь @{message.from_user.username} предложил \"{i}\" трек с ненормативной лексикой!')
                            states_pon.append(f"❌ В треке \"{i}\" (Распознанный как \"{visual_name}\") была найдена ненормативная лексика!\n")
                            additionals.suggest_music(False, message.from_user.id, f"{track['id']}", visual_name)

                        elif track_form:
                            logging.warning(f'✅ Пользователь @{message.from_user.username} предложил \"{i}\" трек и он был добавлен!')
                            states_pon.append(f"✅ Трек \"{i}\" (Распознанный как \"{visual_name}\") добавлен в список возможной музыки!\n")
                            additionals.suggest_music(True, message.from_user.id, f"{track['id']}", visual_name)


                    elif track_swearing:
                        logging.warning(f'❌ Пользователь @{message.from_user.username} предложил \"{i}\" трек с ненормативной лексикой!')
                        states_pon.append(f"❌ В треке \"{i}\" (Распознанный как \"{visual_name}\") была найдена ненормативная лексика!\n")
                        additionals.suggest_music(False, message.from_user.id, f"{track['id']}", visual_name)
                    else:
                        logging.warning(f'✅ Пользователь @{message.from_user.username} предложил \"{i}\" трек и он был добавлен!')
                        states_pon.append(f"✅ Трек \"{i}\" (Распознанный как \"{visual_name}\") добавлен в список возможной музыки!\n")
                        additionals.suggest_music(True, message.from_user.id, f"{track['id']}", visual_name)


                else:
                    logging.warning(f'❌ Пользователь @{message.from_user.username} предложил \"{i}\" трек с ненормативной лексикой!')
                    states_pon.append(f"❌ В названии трека \"{i}\" была найдена ненормативная лексика!\n")

        else:
            logging.warning(f'❌ Пользователь @{message.from_user.username} предложил \"{i}\" название трека с ненормативной лексикой!')
            states_pon.append(f"❌ В названии трека \"{i}\" была найдена ненормативная лексика!\n")

        query = '\n'.join(states_pon)
        await message_query.edit_text(f"Парсинг треков...\n<blockquote expandable>{query}</blockquote>")

    await message_query.edit_text(f"Треки были проверены!\n<blockquote expandable>{query}</blockquote>"
                                  f"\n🔹Предложенные вами треки и их состояния можно удалить в профиле /profile"
                                  f"\n🔹Если текст трека не был найден, наш администратор проверит его в течении 48 часов."
                                  f"\n🔹Если трек не был найден вообще, попробуйте указать автора, убедитесь в правильности запроса или проверьте, доступен ли этот трек на Яндекс Музыке.")
    userdata = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    userdata[str(message.from_user.id)]["last_mus"] = int(time.time())
    wwjson.send_json_data(userdata, "jsons/Human_souls.json")
    await state.clear()


async def send_request_to_admins(soul_name: str, track: yandex_music.track.track.Track, soul_id: int, soul_request: str, senter_id: str) -> None:
    """
    в случае, если текст трека не был найден, то отправляет администраторам запрос, разрешить/запретить трек или вообще заблокировать пользователя
    :param soul_name: Юзернейм пользователя
    :param track: Информация трека
    :param soul_id: Айди пользователя
    :param soul_request: То, что ввёл пользователь, чтобы найти трек
    """
    soul_request = soul_request.replace("\n", '')

    artists = ', '.join([i['name'] for i in track['artists']][:3])

    track_pon = await yparse.parse(f"{track['title']}")

    human_soul = dict(wwjson.get_json_data("jsons/Human_souls.json"))[str(soul_id)]


    await yparse.download_mus(track_pon)

    buttons = [
        [
            types.InlineKeyboardButton(text="✅", callback_data=f"track_{track['id']}_{senter_id}_allow"),
            types.InlineKeyboardButton(text="❌", callback_data=f"track_{track['id']}_{senter_id}_forbid")
        ],
        [
            types.InlineKeyboardButton(text=f"⛔ Заблокировать @{soul_name}", callback_data=f"block_user_{soul_id}")
        ]
    ]
    keyboard_pon = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    audio_file = FSInputFile(path=f'{track["id"]}.mp3')

    for e, i in enumerate(wwjson.get_admins_list()):
        await bot.send_audio(i,
                audio=audio_file,
                caption=f"Душа @{soul_name} из {human_soul['class']} класса, предлагает трек \"{track['title']}-({artists})\"\n(по запросу: {soul_request})",
                reply_markup=keyboard_pon)


    os.remove(f'{track["id"]}.mp3')


@dp.callback_query(lambda c: c.data.startswith("track_"))
@decorators.catch_errors
async def track_allow(callback_query: types.CallbackQuery) -> None:
    """
    Обрабатывает разрешение/запрет трека от администрации
    """
    track_title = callback_query.data.split("_")[1]
    senter_id = callback_query.data.split("_")[2]
    action = callback_query.data.split("_")[3]
    visual_name = wwjson().get_track_name(track_title)

    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    if human_souls[senter_id]["suggested_music"][track_title] is not None:
        await callback_query.message.answer('Данный трек уже был оценён!')
        await callback_query.answer()
        return None

    if action == "allow":
        human_souls[senter_id]["suggested_music"][track_title] = True
        for i in wwjson.get_admins_list():
            await bot.send_message(i, f"✅ Трек {visual_name} был успешно одобрен админом @{callback_query.from_user.username}!")
        logging.warning(f"✅ Трек {visual_name} был успешно одобрен админом @{callback_query.from_user.username}!")

    elif action == "forbid":
        human_souls[senter_id]["suggested_music"][track_title] = False
        for i in wwjson.get_admins_list():
            await bot.send_message(i, f"❌ Трек {visual_name} был успешно отменён админом @{callback_query.from_user.username}!")
        logging.warning(f"❌ Трек {visual_name} был успешно отменён админом @{callback_query.from_user.username}!")

    wwjson.send_json_data(human_souls, "jsons/Human_souls.json")
    await callback_query.answer()


@dp.callback_query(lambda c: c.data.startswith("block_user_"))
async def block_user(callback_query: types.CallbackQuery) -> None:
    """
    Блокирует пользователя
    """
    userid = callback_query.data.split("_")[2]
    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    username = userid
    for i in human_souls:
        if i == userid:
            username = human_souls[i]["soul_name"]
            break

    human_souls[str(userid)]["usertype"] = "blocked"
    wwjson.send_json_data(human_souls, "jsons/Human_souls.json")
    for i in wwjson.get_admins_list():
        logging.warning(f"❗Пользователь @{username} был успешно заблокирован администратором @{callback_query.from_user.username}!")
        await bot.send_message(i, f"❗Пользователь @{username} был успешно заблокирован администратором @{callback_query.from_user.username}!")
    await callback_query.answer()


@dp.message(decorators.block_filter(), Command("profile"))
@decorators.catch_errors
async def profile(message: Message) -> None:
    """
    Выводит данные человека самому себе
    Команда: /profile
    """
    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    all_user_tracks = []
    for e, i in enumerate(human_souls[str(message.from_user.id)]["suggested_music"].keys()):
        if human_souls[str(message.from_user.id)]["suggested_music"][i] is None:
            icon = "❔"
        elif human_souls[str(message.from_user.id)]["suggested_music"][i]:
            icon = "✅"
        elif not human_souls[str(message.from_user.id)]["suggested_music"][i]:
            icon = "❌"
        i = wwjson().get_track_name(i)
        all_user_tracks.append(f"{e+1}. {i}   -   {icon}")

    all_user_tracks = "\n".join(all_user_tracks)

    user_class = human_souls[str(message.from_user.id)]["class"]
    tracks_len = len(list(human_souls[str(message.from_user.id)]["suggested_music"].keys()))

    buttons = [[types.InlineKeyboardButton(text="🗑️ Удалить трек", callback_data="choose_delete_track")]]
    keyboard_pon = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        f"Профиль @{message.from_user.username}"
        f"\nКласс: {user_class}"
        f"\nКол-во предложенных треков: {tracks_len}"
        f"\n\n<blockquote expandable>{all_user_tracks}</blockquote>"
        '\n❌ - трек был запрещён, \n✅ - трек был разрешён, \n❔ - трек на рассмотрении'
    , reply_markup=keyboard_pon)

class Delete_track(StatesGroup):
    waiting_name = State()

@dp.callback_query(lambda c: c.data == "choose_delete_track")
async def delete_track(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """
    Спрашивает у пользователя, какой трек удалить
    """
    builder = ReplyKeyboardBuilder()

    human_souls_data = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    user_tracks = human_souls_data[str(callback_query.from_user.id)]["suggested_music"]
    if user_tracks:
        for i in user_tracks:
            i = wwjson().get_track_name(i)
            builder.add(types.KeyboardButton(text=str(i)))
        builder.adjust(4)
        builder.row(KeyboardButton(text="Отменить"))

        await callback_query.message.answer(
            "Выберите трек:",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
        await state.set_state(Delete_track.waiting_name)
    else:
        await callback_query.message.answer("❗ Вы не предложили ни одного трека!")
        return None
    await callback_query.answer()


@dp.message(Delete_track.waiting_name)
async def delete_track_(message: Message, state: FSMContext) -> None:
    """
    Удаляет трек
    """
    track = wwjson().get_track_id(message.text)
    track_name = message.text
    if track_name == 'Отменить':
        mess = await message.answer(f"Отмена...", reply_markup=aiogram.types.ReplyKeyboardRemove())
        await state.clear()
        await mess.delete()
        return None
    human_souls_data = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    if track in human_souls_data[str(message.from_user.id)]["suggested_music"]:
        logging.warning(f'Пользователь {message.from_user.username} удалил тек \"{track_name}\"!')
        del human_souls_data[str(message.from_user.id)]["suggested_music"][str(track)]
    else:
        await message.answer(f"❗ Трек {track_name} не был найден!", reply_markup=aiogram.types.ReplyKeyboardRemove())
        await state.clear()
        return None

    wwjson.send_json_data(human_souls_data, "jsons/Human_souls.json")

    await message.answer(f"✅ Трек {track_name} был успешно удалён!", reply_markup=aiogram.types.ReplyKeyboardRemove())
    await state.clear()




@dp.message(decorators.block_filter(), Command("top"))
@decorators.catch_errors
async def top(message: Message) -> None:
    """
    Выводит топ треков
    """
    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon = (
        wwjson().know_top20_music(human_souls[str(message.from_user.id)]["class"])
    )
    TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon = \
        [
            f"{'-'.join(i.split('-')[:-1])} / <i>{'-'.join(i.split('-')[-1:]).replace(')', '').replace('(', '')}</i> : {TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon[i]}"
            for i in
            TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon
        ]

    TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon = ''.join(
        (f"🔴 {el}" if i == 0 else
        f"\n 🟠 {el}" if i == 1 else
        f"\n  🟡 {el}" if i == 2 else
        f"\n  🔵 {el}")
        for i, el in enumerate(
            TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon)
    )
    if TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon == "":
        TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon = "Треки не были найдены!"

    top_tracks = human_souls[str(message.from_user.id)]["class"]
    await message.answer(
        f"👑 Топ 20 треков {top_tracks} классов:"
        f"\n\n{TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon}"
    )


#хз чо это, какаята main залупа чтобы бот запустился
async def main() -> None:
    global yparse
    connect_stat = True

    while True:
        try:
            client = await ClientAsync(token="y0__xD7ganyBRje-AYgicPntBL0uWtUHnAsJBHTkC-I29OiaSJPeg").init()
            yparse = Yparse(client)

        except yandex_music.exceptions.TimedOutError:
            logging.warning("Connection timed out. Waiting for 60 seconds...")
            connect_stat = False
            await asyncio.sleep(60)

        except yandex_music.exceptions.NetworkError:
            logging.warning("Connection connection is missing. Waiting for 60 seconds...")
            connect_stat = False
            await asyncio.sleep(60)

        else:
            if not connect_stat:
                logging.warning("Connection is established!")
                client = await ClientAsync(token="y0__xD7ganyBRje-AYgicPntBL0uWtUHnAsJBHTkC-I29OiaSJPeg").init()
                yparse = Yparse(client)
            break

    dp.include_router(my_admins_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


# запуск
if __name__ == "__main__":
    coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'}, 'levelname': {'color': 'green'}, 'name': {'color': 'blue'}}
    coloredlogs.DEFAULT_LEVEL_STYLES = {'critical': {'bold': True, 'color': 'red'}, 'debug': {'color': 'white'}, 'error': {'color': 'red'}, 'info': {'color': 'white'}, 'notice': {'color': 'magenta'}, 'spam': {'color': 'green', 'faint': True}, 'success': {'bold': True, 'color': 'green'}, 'verbose': {'color': 'blue'}, 'warning': {'color': 'yellow'}}
    coloredlogs.install(level=logging.INFO, stream=sys.stdout, format='%(asctime)s : %(levelname)s : %(message)s')
    asyncio.run(main())