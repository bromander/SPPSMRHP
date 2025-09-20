import json
import logging
from typing import Optional, Union
from yandex_music.exceptions import NotFoundError
import yandex_music
from profanityfilter import ProfanityFilter
import string
from collections import Counter

pf = ProfanityFilter(languages=['ru', 'en'])

with open("ru_curse_words.txt", "r", encoding="UTF-8") as ru_CURSEWORDS:
    CURSEWORDS = ru_CURSEWORDS.read().split("\n")
with open("ru_abusive_words.txt", "r", encoding="UTF-8") as ru_CURSEWORDS:
    CURSEWORDS += ru_CURSEWORDS.read().split("\n")
with open("en_curse_words.json", "r", encoding="UTF-8") as en_CURSEWORDS:
    CURSEWORDS += json.load(en_CURSEWORDS)


class Work_with_json:

    @staticmethod
    def get_usertype(userid: str) -> str:
        """
        :param userid: айди пользователя
        :return: тип пользователя
        """
        with open("jsons/Human_souls.json", "r", encoding="UTF-8") as file_data:
            file_data = json.load(file_data)
        return file_data[str(userid)]["usertype"]

    @staticmethod
    def get_admins_list() -> list[str]:
        """
        :return: список айди всех администраторов
        """
        with open("jsons/Human_souls.json", "r", encoding="UTF-8") as file_data:
            file_data = json.load(file_data)
        admins = [i for i in file_data if file_data[i]["usertype"] in ["admin", "super_admin"]]
        return admins

    @staticmethod
    def is_user_admin(userid: str, what_type:list[str] = ["admin", "super_admin"]) -> bool:
        """
        Проверяет свляется ли пользователь администратором
        :param userid: Айди пользователя
        :param what_type: список проверяемых типов пользователя
        :return: True - тип пользователя в списке, False - тип пользователя не соответствует
        """
        with open("jsons/Human_souls.json", "r", encoding="UTF-8") as file_data:
            file_data = json.load(file_data)
        return file_data[str(userid)]["usertype"] in what_type


    @staticmethod
    def get_json_data(path:str, type_load:str="r", encoding:str="UTF-8") -> any:
        """
        Выдаёт данные json файла
        :param path: Путь к файлу
        :param type_load: тип загрузки
        :param encoding: кодирование
        :return: данные файла
        """
        with open(path, type_load, encoding=encoding) as file_data:
            return json.load(file_data)

    @staticmethod
    def send_json_data(content:any, path: str, type_load: str = "w", encoding: str = "UTF-8") -> None:
        """
        Загружает в json файл данные
        :param content: данные, которые будут загруженны
        :param path: Путь к файлу
        :param type_load: Тип загрузки
        :param encoding: кодирование
        """
        with open(path, type_load, encoding=encoding) as file_data:
            return json.dump(content, file_data, indent=4, ensure_ascii=False)


    def already_have_that_track(self, track_name: str):
        """
        Проверяет, есть ли уже такой трек
        :param track_name: Название трека
        :return: Данные трека
        """
        human_souls = self.get_json_data("jsons/Human_souls.json")

        for soul in human_souls.values():
            music = soul["suggested_music"].get(track_name)
            if music is not None:
                return music

        return "TrackNotFoundError"

    def get_track_name(self, track_id: str, path="jsons/data.json") -> str:
        try:
            return str(self.get_json_data(path)["tracks"][str(track_id)])
        except KeyError:
            return str(track_id)

    def get_track_id(self, track_name: str, path="jsons/data.json") -> str:
        tracks = self.get_json_data(path)["tracks"]
        for i in tracks:
            if tracks[i] == track_name:
                return i

    def set_track_name(self, track_id: str, track_name: str, path="jsons/data.json") -> None:
        tracks_names = dict(self.get_json_data(path))
        tracks_names["tracks"][track_id] = track_name
        self.send_json_data(tracks_names, path)


    def know_top20_music(self, class_pon: int) -> dict:
        """
        Выдаёт топ 20 треков, сортируя их по количеству
        :param class_pon: шкильный класс
        :return: 20 самых популярити треков
        """
        human_souls = self.get_json_data("jsons/Human_souls.json")
        counter = Counter()

        for soul in human_souls.values():
            if soul["class"] == class_pon:
                for track, music in soul["suggested_music"].items():
                    if music:  # != None / пустому
                        name = self.get_track_name(track)
                        counter[name] += 1

        return dict(counter.most_common(20))


class Yandex_music_parse:
    def __init__(self, client):
        self.client = client

    async def parse(self, query: str) -> dict:
        """
        Парсит трек на яндекс музыке
        :param query: название трека
        :return: словарь с данными самого подходящего трека
        """
        search_res = await self.client.search(query, type_='track')
        first_short = search_res.tracks.results[0]

        return first_short

    @staticmethod
    async def download_mus(first_short: yandex_music.track.track.Track) -> None:
        """
        Скачивает трек
        :param first_short: Данные трека
        """
        await first_short.download_async(f'./{first_short["id"]}.mp3')


    async def check_mus_for_swearing(self, first_short: yandex_music.track.track.Track) -> Union[str, bool]:
        """
        Проверяет трек на наличие нецензурных выражений
        :return: bool/Exception/"NotFoundError"
        """
        try:
            lyrics_info = await first_short.get_lyrics_async()
            text = await lyrics_info.fetch_lyrics_async()
            return await self.check_text_for_swearing(text)
        except NotFoundError:
            return "NotFoundError"
        except Exception as e:
            raise e

    @staticmethod
    async def check_text_for_swearing(text: str) -> bool:
        """
        Проверяет текст на наличие нецензурных выражений
        :param text: Текст
        :return: True - есть мат, False - нет мата
        """

        text = text.translate(str.maketrans('', '', string.punctuation))
        words = text.upper().split()

        for curse in CURSEWORDS:
            if curse.upper() in words:
                logging.warning(f"Нецензурное слово: {curse}")
                return True
        return False


def suggest_music(state: Optional[bool], user_id: Union[int, str], track_id: str, track_name = None) -> None:
    '''
    Записывает трек в данные игрока
    :param state: True - разрешён, False - Запрещён, None - ждёт разрешения администрации
    :param user_id: айди пользователя
    :param track_id: название трека
    '''
    human_souls = Work_with_json().get_json_data("jsons/Human_souls.json")
    human_souls[str(user_id)]["suggested_music"][track_id] = state
    Work_with_json().send_json_data(human_souls, "jsons/Human_souls.json")

    if track_name:
        Work_with_json().set_track_name(track_id, track_name)

if __name__ == "__main__":
    pass