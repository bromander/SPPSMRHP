import os
import asyncio
import logging
import sys
import random

from pyexpat.errors import messages
from yandex_music import ClientAsync
import time
from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, TelegramObject
from aiogram.fsm.state import State, StatesGroup
from skripts import additionals
from skripts.additionals import Work_with_json as wwjson, Yandex_music_parse as Yparse
from aiogram.fsm.context import FSMContext
from git import Repo
import tempfile, shutil

PENDING_REQUESTS = {}
TOKEN = "7559789537:AAHvjxbEEmQ46w4ACdDoeJ2tQSlp3lZsolk"
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

admins_ids = [5389197909, 6113046557]


def block_filter():
    async def _filter(message: Message) -> bool:
        try:
            userdata = wwjson.get_json_data("jsons/Human_souls.json")[str(message.from_user.id)]
        except KeyError:
            return True

        if userdata["class"] == 0:
            await message.answer("Ошибка, вы не ввели свой возраст!\nНапишите команду /start чтобы настроить СВОй профиль!")
            return False


        if userdata["soul_name"] != "br0mand":
            return userdata["blocked"] == False
        else:
            return True

    return _filter



@dp.message(Command("bot_info"))
async def send_info(message: Message):
    def count_commits_gitpython(repo_path: str) -> int:
        repo = Repo(repo_path)
        commits = list(repo.iter_commits('master'))
        last_commit = repo.head.commit
        return len(commits), last_commit

    vers, last_comit_data = count_commits_gitpython(r"C:\Users\roma\PycharmProjects\SPPSMRHP")

    start_time = time.perf_counter()
    message_before_ping = await message.answer(f'Альфредо 19 \n'
                         f'Версия: V1.{vers}\n'
                         f'---------------------\n'
                         f'Последнее обновление: {last_comit_data.committed_datetime}\n• {last_comit_data.message.strip()}\n\n'
                         f"Пинг: Загрузка...")
    end_time = time.perf_counter()
    latency = (end_time - start_time) * 1000

    await message_before_ping.edit_text(f'Альфредо 19 \n'
                         f'Версия: V1.{vers}\n'
                         f'---------------------\n'
                         f'Последнее обновление: {last_comit_data.committed_datetime}\n• {last_comit_data.message.strip()}\n\n'
                         f"Пинг: {latency:.2f} мс")



#Комманда Start
@dp.message(Command("start"))
async def start_command(message: Message):
    human_souls_data = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    if str(message.from_user.id) not in list(human_souls_data.keys()):

        logging.info(f"New user! (@{message.from_user.username})")

        human_souls_data[str(message.from_user.id)] = {
            "soul_name" : message.from_user.username,
            "blocked" : False,
            "suggested_music" : {},
            "class" : 0,
            "last_mus" : 0
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


@dp.callback_query(lambda c: c.data.startswith("set_class_"))
async def set_class_(callback_query: types.CallbackQuery):

    class_pon = str(callback_query.data).split("_")[2]
    human_souls_data = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    human_souls_data[str(callback_query.from_user.id)]["class"] = int(class_pon)

    wwjson.send_json_data(human_souls_data, "jsons/Human_souls.json")

    await callback_query.answer()
    await callback_query.message.answer("Команды бота:\n\n/music - предложить музыку\n/profile - Ваш профиль в боте\n/top - топ треков\n/bot_info - тех информация о боте")


class Waiting(StatesGroup):
    waiting_for_music = State()


@dp.message(block_filter(), Command("music"))
async def music(message: Message, state: FSMContext):
    userdata = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    if time.time() - int(userdata[str(message.from_user.id)]["last_mus"]) > 30:
        await message.answer("Введите название вашего трека/треков через запятую:")
        await state.set_state(Waiting.waiting_for_music)
        userdata[str(message.from_user.id)]["last_mus"] = int(time.time())
        wwjson.send_json_data(userdata, "jsons/Human_souls.json")

    else:
        await message.answer(f"Вы делаете слишком частые запросы!\nПожалуйста, подождите {30 - int(time.time() - int(userdata[str(message.from_user.id)]["last_mus"]))} сек")

@dp.message(Waiting.waiting_for_music)
async def waiting_for_music(message: Message, state: FSMContext):
    states_pon = []
    musics = message.text.split(",")

    query = '\n'.join(states_pon)
    message_query = await message.answer(f"Загрузка...\n<blockquote expandable>{query}</blockquote>")

    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    for i in musics:
        track_swearing = await yparse.check_text_for_swearing(str(i))
        if track_swearing == False:
            try:
                track = await yparse.parse(i)

            except AttributeError:
                states_pon.append(f"⛔ Трек \"{i}\" не был найден!\n")

            else:

                track_swearing = await yparse.check_text_for_swearing(str(i))
                if track_swearing == False:
                    track_swearing = await yparse.check_mus_for_swearing(track)
                    artists = ', '.join([i['name'] for i in track['artists']][:3])

                    if track_swearing == "NotFoundError":

                        track_form = wwjson().already_have_that_track(f"{track['title']}-({artists})")

                        if track_form == "TrackNotFoundError":
                            states_pon.append(f"❔ Текст трека \"{i}\" (Распознанного как \"{track['title']}-({artists})\") не был найден!\n")
                            additionals.suggest_music(None, message.from_user.id, f"{track['title']}-({artists})")
                            await send_request_to_admins(message.from_user.username, track, message.from_user.id, i)

                        elif track_form == False:
                            states_pon.append(f"❌ В треке \"{i}\" (Распознанного как \"{track['title']}-({artists})\") была найдена ненормативная лексика!\n")
                            additionals.suggest_music(False, message.from_user.id, f"{track['title']}-({artists})")

                        elif track_form == True:
                            states_pon.append(f"✅ Трек \"{i}\" (Распознанного как \"{track['title']}-({artists})\") добавлен в список возможной музыки!\n")
                            additionals.suggest_music(True, message.from_user.id, f"{track['title']}-({artists})")


                    elif track_swearing:
                        states_pon.append(f"❌ В треке \"{i}\" (Распознанного как \"{track['title']}-({artists})\") была найдена ненормативная лексика!\n")
                        additionals.suggest_music(False, message.from_user.id, f"{track['title']}-({artists})")
                    else:
                        states_pon.append(f"✅ Трек \"{i}\" (Распознанного как \"{track['title']}-({artists})\") добавлен в список возможной музыки!\n")
                        additionals.suggest_music(True, message.from_user.id, f"{track['title']}-({artists})")


                else:
                    states_pon.append(f"❌ В названии трека \"{i}\" была найдена ненормативная лексика!\n")
                    additionals.suggest_music(False, message.from_user.id, f"{track['title']}-({artists})")

        else:
            states_pon.append(f"❌ В названии трека \"{i}\" была найдена ненормативная лексика!\n")

        query = '\n'.join(states_pon)
        await message_query.edit_text(f"Парсинг треков...\n<blockquote expandable>{query}</blockquote>")

    await message_query.edit_text(f"Треки были проверены!\n<blockquote expandable>{query}</blockquote>"
                                  f"\n🔹Если текст трека не был найден, наш администратор проверит ваш трек в течении 48 часов."
                                  f"\n🔹Состояние ваших треков можно увидеть в команде /profile"
                                  f"\n🔹Если трек не был найден вообще, попробуйте указать автора или удостоверьтесь в правильности запроса")

    await state.clear()


async def send_request_to_admins(soul_name, track, soul_id, soul_request):
    global PENDING_REQUESTS

    artists = ', '.join([i['name'] for i in track['artists']][:2])
    PENDING_REQUESTS[len(PENDING_REQUESTS)] = f"{track['title']}-({artists})"

    buttons = [
        [
            types.InlineKeyboardButton(text="✅", callback_data=f"track_{len(PENDING_REQUESTS)}_allow"),
            types.InlineKeyboardButton(text="❌", callback_data=f"track_{len(PENDING_REQUESTS)}_forbid")
        ],
        [
            types.InlineKeyboardButton(text=f"⛔ Заблокировать @{soul_name}", callback_data=f"block_user_{soul_id}")
        ]
    ]
    keyboard_pon = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    for i in admins_ids:
        await bot.send_message(i, f"Душа @{soul_name} предлагает трек \"{track['title']}-({artists})\"\n(по запросу: {soul_request})", reply_markup=keyboard_pon)


@dp.callback_query(lambda c: c.data.startswith("track_"))
async def track_allow(callback_query: types.CallbackQuery):
    track_title = callback_query.data.split("_")[1]
    action = callback_query.data.split("_")[2]

    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    print(PENDING_REQUESTS)

    if action == "allow":
        human_souls[str(callback_query.from_user.id)]["suggested_music"][PENDING_REQUESTS[int(track_title)-1]] = True
        await callback_query.message.answer(f"✅ Трек {PENDING_REQUESTS[int(track_title)-1]} был успешно одобрен!")
    elif action == "forbid":
        await callback_query.message.answer(f"✅ Трек {PENDING_REQUESTS[int(track_title)-1]} был отменён!")
        human_souls[str(callback_query.from_user.id)]["suggested_music"][PENDING_REQUESTS[int(track_title)-1]] = False

    wwjson.send_json_data(human_souls, "jsons/Human_souls.json")


    await callback_query.answer()


@dp.callback_query(lambda c: c.data.startswith("block_user_"))
async def block_user(callback_query: types.CallbackQuery):

    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))
    human_souls[str(callback_query.from_user.id)]["blocked"] = True
    wwjson.send_json_data(human_souls, "jsons/Human_souls.json")
    await callback_query.message.answer("❗Пользователь был успешно заблокирован!")
    await callback_query.answer()


@dp.message(block_filter(), Command("profile"))
async def profile(message: Message):
    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    all_user_tracks = []
    for i in human_souls[str(message.from_user.id)]["suggested_music"].keys():
        if human_souls[str(message.from_user.id)]["suggested_music"][i] == False:
            icon = "❌"
        elif human_souls[str(message.from_user.id)]["suggested_music"][i] == True:
            icon = "✅"
        elif human_souls[str(message.from_user.id)]["suggested_music"][i] == None:
            icon = "❔"
        all_user_tracks.append(f"{i}   -   {icon}")

    all_user_tracks = "\n\n".join(all_user_tracks)

    await message.answer(
        f"Профиль @{message.from_user.username}"
        f"\nКласс: {human_souls[str(message.from_user.id)]["class"]}"
        f"\nКол-во предложенных треков: {len(list(human_souls[str(message.from_user.id)]["suggested_music"].keys()))}"
        f"<blockquote expandable>{all_user_tracks}</blockquote>"
    )

@dp.message(block_filter(), Command("top"))
async def top(message: Message):
    human_souls = dict(wwjson.get_json_data("jsons/Human_souls.json"))

    TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon = (
        wwjson().know_top50_music(human_souls[str(message.from_user.id)]["class"])
    )

    TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon = \
        [f"{f"{"-".join(i.split("-")[:-1])} / <i>{"-".join(i.split("-")[-1:]).replace(")", "").replace("(", "")}</i>"} : {TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon[i]}"
         for i in TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon]

    TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon = ''.join(
        (f"🔴 {el}" if i == 0 else
         f"\n 🟠 {el}" if i == 1 else
         f"\n  🟡 {el}" if i == 2 else
         f"\n  🔵 {el}")
        for i, el in enumerate(
            TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon)
    )

    await message.answer(
        f"👑 Топ 20 треков {human_souls[str(message.from_user.id)]["class"]} классов:"
        f"\n\n{TOP_20_SOUNDS_DONT_LOOSE_IT_OMG_OMG_OMG_WHAT_TO_HELL_OH_MY_GOT_IS_THAT_REALLY_7777_1488_pon_pon_pon_pon_pon}"
    )


#хз чо это, какаята main залупа чтобы бот запустился
async def main():
    global yparse

    client = await ClientAsync(token="y0__xD7ganyBRje-AYgicPntBL0uWtUHnAsJBHTkC-I29OiaSJPeg").init()

    yparse = Yparse(client)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


#запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())