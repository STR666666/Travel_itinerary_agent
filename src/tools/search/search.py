import time
from langchain.utilities import SerpAPIWrapper
from langchain.tools import tool, HumanInputRun
from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper
from src.utils.readkey import readkey, construct_rapid_headers
from src.utils import global_value
import http, requests
import os

@tool
def google_search(question: str):
    """The description is as follows:
    args:
        -question: the general question you want to ask
    return:
        search result that comes from google search engine
    functionality:
        This tool can be used to search for latest information that relates to a general question
    usage example:
        Action: google_search
        Action Input: xxx
    composition instructions:
        This tool is the last resort, if other tools can't help
    """
    config = readkey()
    os.environ["SERPAPI_API_KEY"] = config["SERP"]["SERPAPI_API_KEY"]
    try:
        search = SerpAPIWrapper()
        res = search.run(question)
    except BaseException:
        res = "invalid response from google"
    return res


@tool
def wolfram_calculator(problem: str):
    """The description is as follows:
    args:
        -problem: the math problem you want to solve, try to use math symbol more
    return:
        the answer to the math problem
    functionality:
        This is a powerful calculator, You can use it to calculate large numbers nand solve complex math problems
    usage example:
        Action: wolfram_calculator
        Action Input: xxx
    composition instructions:
        You should write the problem into math symbol format before you call this tool
    """
    config = readkey()
    os.environ["WOLFRAM_ALPHA_APPID"] = config["WolframAlpha"]["WOLFRAMALPHA_APP_ID"]
    try:
        wolfram = WolframAlphaAPIWrapper()
        res = wolfram.run(problem)
    except BaseException:
        res = "invalid response from wolfram"
    return res

@tool
def bing_entity_search(entity: str) -> str:
    """The description is as follows:
    args:
        -entity: the entity you want to search for
    return:
        the information about the entity
    functionality:
        This tool can be used to acquire an entity's latest information
    usage example:
        Action: bing_entity_search
        Action Input: xxx
    """

    url = "https://bing-entity-search.p.rapidapi.com/entities"

    querystring = {"q":entity,"mkt":"en-us"}

    headers = construct_rapid_headers("bing-entity-search.p.rapidapi.com")
    response = requests.get(url, headers=headers, params=querystring)
    res_text = ""
    if "entities" not in response.json():
        return "No information about this entity."
    for entity in response.json()["entities"]["value"]:
        if "description" in entity:
            res_text = res_text + entity["description"]
    if res_text == "":
        return "No information about this entity."
    else:
        return res_text