import json
import time
from langchain.tools import tool
from src.agent.prompt_template import GeneralPromptTemplate
from src.utils import global_value
from src.agent.travel_agent import TravelAgent
from loguru import logger
from langchain.chat_models import ChatOpenAI
from langchain import LLMChain

PLAN_MODEL = "gpt-4-0613"
def _log_info(info, debug=False):
    if debug:
        logger.debug(info)

def _arg_check(info_dict: str, *args):
    try:
        info_dict = json.loads(info_dict)
    except BaseException:
        return False

    for arg in args:
        if arg not in info_dict:
            return False
    return True


@tool
def chat_to_user(utterance_to_user: str) -> str:
    """The description is as follows:
    args:
        -utterance_to_user: The utterance_to_user argument is a dictionary that contains the following 2 parameters.
        AI_utterance: This is what you want to say to the user.
        user_id: The unique id of the user. This will be given to you in the first message of the user.
        The input to this tool must be in this format:
        {"AI_utterance": "xxx", "user_id": "xxx"}
    return:
        The user's response to you
    usage example:
        Action: chat_to_user
        Action input: {"AI_utterance": "xxx", "user_id": "xxx"}
    functionality:
        If you need human feedback to make your decision, you can call this tool.
    """
    if not _arg_check(utterance_to_user, "AI_utterance", "user_id"):
        return "Tool arguments wrong"
    utterance_to_user = json.loads(utterance_to_user)
    AI_msg = utterance_to_user['AI_utterance']
    user_id = int(utterance_to_user['user_id'])
    agent = global_value.get_dict_value("agents", user_id)
    agent.UI_info.wait_user_inputs = True
    agent.UI_info.chatbots.append([None, AI_msg])
    while (agent.UI_info.wait_user_inputs):
        time.sleep(0.6)
    return agent.UI_info.user_inputs

@tool
def make_city_itinerary(travel_info: str) -> str:
    """The description is as follows:
    args:
        -travel_info: The travel_info argument is a dictionary that contains the following 5 parameters
        user_id: The unique id of the user. This will be given to you in the first message of user
        departure: The departure city should be like this: city, state/province(optional), country
        destination: The destination city should be like this: city, state/province(optional), country
        duration: The number of days you want to spend in the destination city
        additional_info: additional information about the user, such as what kind of sight or restaurant the user is favored by. what is the purpose of the trip such as a family trip with kids, a honey trip with lover or a trip traveling alone.
        You must collect as much additional information as possible from the user, since the additional information is very important for making a good itinerary for the user.
        The input to this tool must be in this format:
        {"user_id": "xxx", "departure": "xxx", "destination": "xxx", "duration":"xxx", "additional_info":"xxx"}
    return:
        A detailed itinerary in the destination city, which contains flight information, hotel information, restaurants information, famous sights information etc...
    usage example:
        Action: make_city_itinerary
        Action input: {"user_id": "xxx", "departure": "xxx", "destination": "xxx", "duration":"xxx", "additional_info":"xxx"}
    functionality:
        This tool can be used to make a detailed itinerary for users in a specific city.
    composition instructions:
        Before you call this tool, you need to collect these information: departure,destination,days,additional_info.
        Remember this tool can only make a travel plan in a specific city, if user requires a travel plan in a state,
        country or continent, you should call the tool 'make_general_travel_plan' first, then call this tool multiple times
        to make detailed travel plan for each city.
    """
    _arg_check(travel_info, "user_id", "departure", "destination", "duration", "additional_info")
    _log_info(travel_info)
    travel_info = json.loads(travel_info)
    travel_agent = TravelAgent(agent_id=int(travel_info["user_id"]), departure=travel_info["departure"],
                                destination=travel_info["destination"], days=int(travel_info["duration"]),
                                additional_info=travel_info["additional_info"])
    travel_agent.run()
    return "The travel plan in on the right text"

@tool
def make_general_itinerary(travel_info: str) -> str:
    """The description is as follows:
    args:
        -travel_info: The travel_info argument is a dictionary that contains the following 5 parameters
        user_id: The unique id of the user. This will be given to you in the first message of user
        departure: The departure city, should be like this: city, country
        destination: The destination place, should like this: state(optional),country(optional),continent
        duration: The number of days you want to spend on the destination place
        additional_info: additional information about the user, such as what kind of sight or restaurant the user is favored by. what is the purpose of the trip such as a family trip with kids, a honey trip with lover or a trip traveling alone.
        The input to this tool must be in this format:
        {"user_id": "xxx", "departure": "xxx", "destination": "xxx", "duration":"xxx", "additional_info":"xxx"}
    return:
        A general itinerary that can traverse several cities in a country/continent
    usage example:
        Action: make_general_itinerary
        Action input: {"user_id": "xxx", "departure": "xxx", "destination": "xxx", "duration":"xxx", "additional_info":"xxx"}
    functionality:
        This tool can be used to make a general itinerary for users that can traverse several cities in a country/continent,
        If the user doesn't provide which specific city to go to, you can call this tool.
    composition instructions:
        Before you call this tool, you need to collect this information: departure,destination,duration,additional_info.
        Remember this tool can make a general itinerary in a country/continent, if user requires a travel plan in a state,
        country or continent, you should call this tool first, then ask for user's opinion to modify the general itinerary, then call the tool 'make_city_itinerary' multiple times
        to make detailed itinerary for each city.
    """
    _arg_check(travel_info, 'destination', 'duration', 'additional_info')
    travel_info = json.loads(travel_info)
    with open("src/prompts/Travel/make_general_itinerary_prompt.txt") as f:
        travel_prompt = f.read()
    travel_prompt_template = GeneralPromptTemplate(template=travel_prompt,
                                                   input_variables=["destination", "duration", "additional_info"])
    chat_llm = ChatOpenAI(temperature=0, model_name=PLAN_MODEL)
    llm_chain = LLMChain(llm=chat_llm, prompt=travel_prompt_template, verbose=False)
    plan = llm_chain({"destination": travel_info['destination'], "duration": travel_info['duration'],
         "additional_info": travel_info['additional_info']}, return_only_outputs=True)['text']
    return plan