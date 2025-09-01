import json
from typing import Optional, Union
from yandex_music.exceptions import NotFoundError
import yandex_music
from profanityfilter import ProfanityFilter
import string

pf = ProfanityFilter(languages=['ru', 'en'])

class Work_with_json:

    @staticmethod
    def get_json_data(path:str, type_load:str="r", encoding:str="UTF-8") -> any:
        '''
        Выдаёт данные json файла
        :param path: Путь к файлу
        :param type_load: тип загрузки
        :param encoding: кодирование
        :return: данные файла
        '''
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
        '''
        Проверяет, есть ли уже такой трек
        :param track_name: Название трека
        :return: Данные трека
        '''
        human_souls = dict(self.get_json_data("jsons/Human_souls.json"))
        for i in human_souls.keys():
            if track_name in list(human_souls[i]["suggested_music"].keys()):
                if human_souls[i]["suggested_music"][track_name] == None:
                    continue
                else:
                    return human_souls[i]["suggested_music"][track_name]
        return "TrackNotFoundError"


    def know_top20_music(self, class_pon: int) -> dict:
        '''
        Выдаёт топ 20 треков, сортируя их по количеству
        :param class_pon: шкильный класс
        :return: 20 самых популярити треков
        '''
        top_dict = {}
        human_souls = dict(self.get_json_data("jsons/Human_souls.json"))
        for i in human_souls.keys():
            if human_souls[i]["class"] == class_pon:
                for o in human_souls[i]["suggested_music"].keys():
                    if human_souls[i]["suggested_music"][o] == True:
                        if o not in top_dict.keys():
                            top_dict[o] = 1
                        else:
                            top_dict[o] += 1
        top_dict = dict(sorted(top_dict.items(), key=lambda item: item[1], reverse=True))

        return dict(list(top_dict.items())[:20])



class Yandex_music_parse:
    def __init__(self, client):
        self.client = client

    async def parse(self, query: str) -> dict:
        '''
        Парсит трек на яндекс музыке
        :param query: название трека
        :return: словарь с данными самого подходящего трека
        '''
        search_res = await self.client.search(query, type_='track')
        first_short = search_res.tracks.results[0]

        return first_short

    @staticmethod
    async def download_mus(first_short: yandex_music.track.track.Track) -> None:
        '''
        Скачивает трек
        :param first_short: Данные трека
        '''
        artists = "_".join([i["name"] for i in first_short['artists']][:3])
        await first_short.download_async(f'./{first_short["title"]}-({artists}).mp3')


    async def check_mus_for_swearing(self, first_short: yandex_music.track.track.Track) -> Union[str, bool]:
        '''
        Проверяет трек на наличие нецензурных выражений
        :return: bool/Exception/"NotFoundError"
        '''
        try:
            lyrics_info = await first_short.get_lyrics_async()
            text = await lyrics_info.fetch_lyrics_async()
            return await self.check_text_for_swearing(text)
        except NotFoundError:
            return "NotFoundError"
        except Exception as e:
            raise e

    @staticmethod
    # true - есть мат, false - нет мата
    async def check_text_for_swearing(text: str) -> bool:
        '''
        Проверяет текст на наличие нецензурных выражений
        :param text: Текст
        :return: True/False
        '''
        with open("ru_curse_words.txt", "r", encoding="UTF-8") as ru_curse_words:
            ru_curse_words = ru_curse_words.read().split("\n")
        with open("ru_abusive_words.txt", "r", encoding="UTF-8") as ru_abusive_words:
            ru_curse_words += ru_abusive_words.read().split("\n")
        with open("en_curse_words.txt", "r", encoding="UTF-8") as en_curse_words:
            ru_curse_words += en_curse_words.read().split("\n")

        text = text.translate(str.maketrans('', '', string.punctuation))

        for i in ru_curse_words:
            if i.upper() in text.upper().split(' '):
                print(i)
                return True
        return False


def suggest_music(state: Optional[bool], user_id: Union[int, str], track_name: str) -> None:
    '''
    Записывает трек в данные игрока
    :param state: True - разрешён, False - Запрещён, None - ждёт разрешения администрации
    :param user_id: айди пользователя
    :param track_name: название трека
    '''
    human_souls = Work_with_json().get_json_data("jsons/Human_souls.json")
    human_souls[str(user_id)]["suggested_music"][track_name] = state
    Work_with_json().send_json_data(human_souls, "jsons/Human_souls.json")

if __name__ == "__main__":
    pass