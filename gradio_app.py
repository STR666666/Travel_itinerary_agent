import random
import gradio
import gradio as gr
import time
import threading
from src.utils import global_value
from src.agent.chat_agent import Agent
from src.utils.readkey import set_env
from loguru import logger

set_env()
# init global value
global_value._init()
global_value.set_value('agents', {})
# Streaming endpoint
API_URL = "https://api.openai.com/v1/chat/completions"  # os.getenv("API_URL") + "/generate_stream"


def kill_agent(agent_id):
    """
    kill the agent with id 'agent_id' and clear all global value related to this agent
    """
    if len(agent_id) != 0 and global_value.get_dict_value('agents', agent_id[0]) is not None:
        global_value.get_dict_value('agents', agent_id[0]).kill_agent()
        global_value.set_dict_value('agents', agent_id[0], None)
    return [], ""


def reset_agent(agent_id):
    """
    kill the agent with id 'agent_id' and clear all global value related to this agent
    """
    if len(agent_id) != 0 and global_value.get_dict_value('agents', agent_id[0]) is not None:
        global_value.get_dict_value('agents', agent_id[0]).kill_agent()
        global_value.set_dict_value('agents', agent_id[0], None)
    return [], "", gr.update(value="", interactive=False)


def log_info(info, debug=False):
    if debug:
        logger.debug(info)


def start_agent(agent_id, inputs):
    agent = global_value.get_dict_value('agents', agent_id[0])
    if global_value.get_value("user_first_request")==0:
        global_value.set_value("user_first_request",{})
    global_value.set_dict_value('user_first_request', agent_id[0], inputs)
    response = agent.run(inputs + " Remember My user_id is " + str(agent_id[0]))
    agent.UI_info.chatbots.append([None, response["output"]])


def create_agent(agent_id):
    """
    :param agent_id: The agent_id of old agent if existed, or []
    :return: new_agent_id,thinking_process,chat_bot
    """
    kill_agent(agent_id)
    agent_id = [random.randint(0, 100000)]
    while global_value.get_dict_value('agents', agent_id[0]) is not None:
        agent_id = [random.randint(0, 100000)]
    global_value.set_dict_value('agents', agent_id[0],
                                Agent(agent_id=agent_id[0], debug=False, model_name="gpt-4-0613",
                                      visualize_trajectory=True,
                                      tool_path="travel/general_agent_chat.py", mode="ReAct_chat"))
    bot_msg = "I'm a travel assistant. Please describe your travel need."
    agent = global_value.get_dict_value('agents', agent_id[0])
    agent.UI_info.chatbots = [[None, bot_msg]]
    agent.UI_info.travel_plans = []
    log_info(f"create_agent, agent_id is {agent_id[0]}")
    for i in range(len(bot_msg)):
        time.sleep(0.01)
        yield agent_id, [[None, bot_msg[:i + 1]]], ""

    while global_value.get_dict_value('agents', agent_id[0]) is not None:
        time.sleep(1)
        append_thinking_process(agent_id)
        yield agent_id, visualize_chatbot(agent_id), visualize_plan(agent_id)
    return


def append_thinking_process(agent_id):
    agent = global_value.get_dict_value('agents', agent_id[0])
    if len(agent_id) == 0 or agent is None:
        return []

    thinking_process_ori = agent.get_intermediate_steps()
    thinking_process = []
    for action, observation in thinking_process_ori[agent.UI_info.intermediate_step_index:]:
        if "Action: chat_to_user" in action.log:
            continue
        thinking_process += [[None, action.log], [f"API Response:\n{str(observation).strip()}", None]]
    agent.UI_info.intermediate_step_index = len(thinking_process_ori)
    agent.UI_info.chatbots.extend(thinking_process)


def visualize_chatbot(agent_id):
    log_info(f"visualize_chatbot, agent_id is {agent_id}", False)
    if len(agent_id) == 0:
        return []
    agent = global_value.get_dict_value("agents", agent_id[0])
    chatbot = agent.UI_info.chatbots if agent is not None else []
    if len(chatbot) > 0:
        if chatbot[-1][-1] is not None:
            res = chatbot[-1][-1].strip()
            chatbot[-1][-1] = res[:-1] if res.endswith('"') else res
    return chatbot


def visualize_plan(agent_id):
    log_info(f"visualize_plan, agent_id is {agent_id}")
    if len(agent_id) == 0:
        return ""
    agent = global_value.get_dict_value("agents", agent_id[0])
    log_info(f"visualize_plan, length of travel plans {len(agent.UI_info.travel_plans)}")
    plans = agent.UI_info.travel_plans if agent is not None else ""
    show_itinerary = ""
    if len(plans) > 0:
        for i, daily_itinerary in enumerate(plans, 1):
            if daily_itinerary.startswith("This is booking information."):
                show_itinerary = show_itinerary + f'\n<h2 align="center">Booking Information</h2><br>\n' + daily_itinerary[28:] + '\n'
            else:
                show_itinerary = show_itinerary + '\n<h2 align="center">Day '+str(i)+"</h2><br>\n"+daily_itinerary+"\n"
    return show_itinerary

def handle_inputs_submit(agent_id, inputs):
    log_info(f"handle_inputs_submit, agent_id is {agent_id}", False)

    agent = global_value.get_dict_value('agents', agent_id[0])
    if not agent.started:
        thread = threading.Thread(target=start_agent, kwargs={"agent_id": agent_id, "inputs": inputs})
        thread.start()

    agent.UI_info.user_inputs = inputs
    agent.UI_info.wait_user_inputs = False
    agent.UI_info.chatbots.append([inputs, None])
    return ""

def activate():
    return gr.update(interactive=True)

title = """<h1 align="center">Have a Trip with Your Private Travel Plan Asistant</h1>"""
# display message for themes feature
theme_addon_msg1 = """<center>Including transportation🛫, accommodation🏠, restaurants🍧 and scenic spots🌋, and completes a unique travel plan in the interaction. Powered by ChatGPT & GPT-4.</center>
"""
theme_addon_msg2 = """<center>❗️Press "Start" first, then enter your trip intention. Press "Reset" to start over.</center>
"""

with gr.Blocks(
        theme=gr.themes.Soft(text_size=gr.themes.sizes.text_sm),
        css="""#col_container { margin-left: auto; margin-right: auto;} #chatbot {height: 420px; overflow: auto;}"""
) as demo:
    gr.Markdown(title)
    gr.Markdown(theme_addon_msg1)
    gr.Markdown(theme_addon_msg2)
    with gr.Column(elem_id="col_container"):
        # Users need to provide their own GPT4 API key, it is no longer provided by Huggingface
        with gr.Row():
            with gr.Column(scale=5):
                chatbot = gr.Chatbot(label='Travel Assistant', elem_id="chatbot")
                inputs = gr.Textbox(placeholder="Interact with your travel assistant.",
                                    label="Type an input and press Enter",interactive=False)
                gr.Examples(
                    examples=[["I'm currently residing in Los Angeles and have an interest in natural views. I plan to embark on a three-day journey to Shanghai."], ["I like architecture."], ["I want to explore Europe for a month and I love ancient architecture. Now I am currently in shanghai."]], inputs=inputs)
                with gr.Row():
                    start = gr.Button(value="Start", variant='primary')
                    reset = gr.Button(value="Reset")
            with gr.Column(scale=5):
                plan = gr.Markdown(label='Itinerary', interactive=False)
    # Event handling
    agent_id = gradio.State([])
    inputs.submit(handle_inputs_submit, [agent_id, inputs],
                  [inputs])
    start.click(create_agent, [agent_id], [agent_id, chatbot, plan])
    start.click(activate, [], [inputs])
    reset.click(reset_agent, [agent_id], [chatbot, plan, inputs])
    demo.title = 'Travel Plan Assitant'

# demo.queue(concurrency_count=5).launch(debug=True, server_name="0.0.0.0", server_port=7870)
demo.queue(concurrency_count=5).launch(debug=True)
