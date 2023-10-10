import os
import configparser

def readkey():
    config_path = "src/utils/apikey.ini"
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def construct_rapid_headers(rapid_host="tripadvisor16.p.rapidapi.com"):
    config = readkey()
    headers = {
        "X-RapidAPI-Key": config["RapidAPI"]["RAPIDAPI_API_KEY"],
        "X-RapidAPI-Host": rapid_host,
        "Connection": "close",
    }
    return headers

def set_env():
    config = readkey()
    os.environ["SERPAPI_API_KEY"] = config["SERP"]["SERPAPI_API_KEY"]
    os.environ["WOLFRAMALPHA_APP_ID"] = config["WolframAlpha"]["WOLFRAMALPHA_APP_ID"]
    os.environ["OPENAI_API_KEY"] = config["OPENAI"]["OPENAI_API_KEY"] if os.environ.get('OPENAI_API_KEY') is None else os.environ["OPENAI_API_KEY"]
    os.environ["GOOGLEMAP_API_KEY"] = config["GoogleMaps"]["GoogleMap_API_KEY"]