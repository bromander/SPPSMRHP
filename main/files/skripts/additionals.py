import json
from json.decoder import JSONDecodeError
from yandex_music.exceptions import NotFoundError
from profanityfilter import ProfanityFilter

pf = ProfanityFilter(languages=['ru', 'en'])

class Work_with_json:

    @staticmethod
    def get_json_data(path:str, type_load:str="r", encoding:str="UTF-8"):
        with open(path, type_load, encoding=encoding) as file_data:
            return json.load(file_data)

    @staticmethod
    def send_json_data(content:any, path: str, type_load: str = "w", encoding: str = "UTF-8"):
        with open(path, type_load, encoding=encoding) as file_data:
            return json.dump(content, file_data, indent=4, ensure_ascii=False)


    def already_have_that_track(self, track_name):
        human_souls = dict(self.get_json_data("jsons/Human_souls.json"))
        for i in human_souls.keys():
            if track_name in list(human_souls[i]["suggested_music"].keys()):
                if human_souls[i]["suggested_music"][track_name] == None:
                    continue
                else:
                    return human_souls[i]["suggested_music"][track_name]
        return "TrackNotFoundError"


    def know_top50_music(self, class_pon):
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

    async def parse(self, query):
        search_res = await self.client.search(query, type_='track')
        first_short = search_res.tracks.results[0]

        return first_short

    @staticmethod
    async def download_mus(first_short):
        artists = "_".join([i["name"] for i in first_short['artists']][:3])
        await first_short.download_async(f'D:/yeah/{first_short["title"]}-({artists}).mp3')


    async def check_mus_for_swearing(self, first_short):
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
    async def check_text_for_swearing(text:str):
        with open("ru_curse_words.txt", "r", encoding="UTF-8") as ru_curse_words:
            ru_curse_words = ru_curse_words.read().split("\n")
        with open("ru_abusive_words.txt", "r", encoding="UTF-8") as ru_abusive_words:
            ru_curse_words += ru_abusive_words.read().split("\n")

        for i in ru_curse_words:
            if i.upper() in text.upper():
                return True
        return False


def suggest_music(state, user_id, track_name):
    human_souls = Work_with_json().get_json_data("jsons/Human_souls.json")
    human_souls[str(user_id)]["suggested_music"][track_name] = state
    Work_with_json().send_json_data(human_souls, "jsons/Human_souls.json")

if __name__ == "__main__":
    pass