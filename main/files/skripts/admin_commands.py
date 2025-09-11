import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message
from skripts import additionals, admin_commands
from skripts.additionals import Work_with_json as wwjson, Yandex_music_parse as Yparse


my_admins_router = Router(name=__name__)



@my_admins_router.message(Command("clear_usersdata"))
async def clear_usersdata(message: Message) -> None:
    if wwjson.is_user_admin(str(message.from_user.id), ['super_admin']):
        usersdata = wwjson.get_json_data("jsons/Human_souls.json")
        for i in usersdata:
            usersdata[str(i)]["suggested_music"] = {}
            usersdata[str(i)]["class"] = 0
        wwjson.send_json_data(usersdata, "jsons/Human_souls.json")
        for i in wwjson.get_admins_list():
            await message.bot.send_message(i, f"🗑️ Пользователь @{message.from_user.username} отчистил данные всех пользователей (предложенные треки и классы)!")
        logging.warning(f"🗑️ Пользователь @{message.from_user.username} отчистил данные всех пользователей(предложенные треки и классы)!")
    else:
        await message.answer("Ты как эту команду узнал?\nСори, но у тебя недостаточно прав на это")



@my_admins_router.message(Command("add_admin"))
async def add_admin(message: Message) -> None:
    if wwjson.is_user_admin(str(message.from_user.id), ['super_admin']):
        user = message.text.split(' ')
        if len(user) != 2:
            await message.answer('Ошибка, вы не ввели ID пользователя!')
            return None
        else:
            try:
                user = int(user[1])
            except ValueError:
                await message.answer('Ошибка, вы ввели не ID пользователя!\n\nId пользователя можно узнать, переслав его сообщение @userinfobot')
                return None
        if wwjson.is_user_admin(str(user), ['super_admin', 'admin']):
            await message.answer('Ошибка, данный пользователь уже является администратором!')
            return None
        user_username = wwjson.get_json_data("jsons/Human_souls.json")[str(user)]["soul_name"]
        usersdata = wwjson.get_json_data("jsons/Human_souls.json")
        for i in wwjson.get_admins_list():
            await message.bot.send_message(int(i), text=f'✅ Пользователь @{message.from_user.username} добавил нового администратора @{user_username}!')
        usersdata[str(user)]["usertype"] = "admin"
        wwjson.send_json_data(usersdata, "jsons/Human_souls.json")
        logging.warning(f'✅ Пользователь @{message.from_user.username} добавил нового администратора @{user_username}!')
    else:
        await message.answer("Ты как эту команду узнал?\nСори, но у тебя недостаточно прав на это")


@my_admins_router.message(Command("del_admin"))
async def del_admin(message: Message) -> None:
    if wwjson.is_user_admin(str(message.from_user.id), ['super_admin']):
        user = message.text.split(' ')
        if len(user) != 2:
            await message.answer('Ошибка, вы не ввели ID пользователя!')
            return None
        else:
            try:
                user = int(user[1])
            except ValueError:
                await message.answer('Ошибка, вы ввели не ID пользователя!\n\nId пользователя можно узнать, переслав его сообщение @userinfobot')
                return None
        if wwjson.is_user_admin(str(user), ['default']):
            await message.answer('Ошибка, данный пользователь не является администратором!')
            return None
        user_username = wwjson.get_json_data("jsons/Human_souls.json")[str(user)]["soul_name"]
        usersdata = wwjson.get_json_data("jsons/Human_souls.json")
        for i in wwjson.get_admins_list():
            await message.bot.send_message(int(i), text=f'✅ Пользователь @{message.from_user.username} удалил администратора @{user_username} из состава!')
        usersdata[str(user)]["usertype"] = "default"
        wwjson.send_json_data(usersdata, "jsons/Human_souls.json")
        logging.warning(f'✅ Пользователь @{message.from_user.username} удалил администратора @{user_username} из состава!')
    else:
        await message.answer("Ты как эту команду узнал?\nСори, но у тебя недостаточно прав на это")




@my_admins_router.message(Command("get_all_users"))
async def get_all_users(message: Message) -> None:
    if wwjson.is_user_admin(str(message.from_user.id)):
        usersdata = wwjson.get_json_data("jsons/Human_souls.json")
        usersdata = dict(sorted(usersdata.items(), key=lambda item: item[1]["class"]))

        for i in usersdata:
            userdata = usersdata[i]

            if int(userdata["last_mus"]) == 0:
                user_last_activity = 'НИКОГДА'
            else:
                user_last_activity = time.ctime(int(userdata["last_mus"]))

            await message.answer(f'Пользователь @{userdata["soul_name"]}'
                                 f'\nID: <i>{i}</i>'
                                 f'\nСтатус пользователя: <i>{userdata["usertype"]}</i>'
                                 f'\nКол-во  предложенных треков: <i>{len(userdata["suggested_music"])}</i>'
                                 f'\nПоследняя активность: <i>{user_last_activity}</i>'
                                 f'\nКласс: <i>{userdata["class"]}</i>')
    else:
        await message.answer("Ты как эту команду узнал?\nСори, но у тебя недостаточно прав на это")


@my_admins_router.message(Command("set_recruiting"))
async def set_recruiting(message: Message) -> None:
    if wwjson.is_user_admin(str(message.from_user.id), ['super_admin']):
        data = wwjson.get_json_data('./jsons/data.json')
        if data["recruiting"]:
            data["recruiting"] = False
            for i in wwjson.get_admins_list():
                await message.bot.send_message(chat_id=i, text="🔒 Набор треков был закрыт!")
            logging.warning(f"🔒 Набор треков был закрыт пользователем {message.from_user.username}!")
        else:
            data["recruiting"] = True
            for i in wwjson.get_admins_list():
                await message.bot.send_message(chat_id=i, text="🔓 Набор треков был открыт!")
            logging.warning(f"🔓 Набор треков был открыт пользователем {message.from_user.username}!")
        wwjson.send_json_data(data, './jsons/data.json')
    else:
        await message.answer("Ты как эту команду узнал?\nСори, но у тебя недостаточно прав на это")