from dataclasses import dataclass
from enum import Enum
from tools.langchain import LLMChain
from tools.langchain.agents import AgentExecutor, LLMSingleActionAgent
from tools.langchain.chat_models import ChatOpenAI
from tools.langchain.evaluation.agents import TrajectoryEvalChain
from src.agent.prompt_template import (
    ReActOutputParser,
    ReActPromptTemplate,
    T5OutputParser,
    T5PromptTemplate,
)
from src.agent.retriever import Retriever


@dataclass
class UIInfo:
    """Class to hold user interface related information."""
    wait_user_inputs: bool = False
    user_inputs: str = ""
    chatbots: list = []
    intermediate_step_index: int = 0
    travel_plans: list = []


class Mode(Enum):
    """Enumeration for different modes of operation."""
    T5 = "T5"
    TRAVEL = "travel"
    REACT_CHAT_PROMPT = "ReAct_chat_prompt"
    REACT_PROMPT = "ReAct_prompt"


class Agent:
    """The agent generates reasoning paths and calls APIs"""

    def __init__(
            self,
            tool_path,
            agent_id=0,
            model_name="gpt-3.5-turbo-16k-0613",
            debug=False,
            visualize_trajectory=True,
            mode=Mode.T5,
    ):
        self.agent_id = agent_id
        self.debug = debug
        self.UI_info = UIInfo()
        self.visualize_trajectory = visualize_trajectory
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, verbose=self.debug)
        self.retriever = Retriever(tool_path=tool_path)
        self.tools = self.retriever.get_tools()

        # Set prompt template and output parser based on the mode
        if mode == Mode.T5:
            self._init_t5_mode()
        elif mode == Mode.TRAVEL:
            self._init_travel_mode()
        elif mode == Mode.REACT_CHAT_PROMPT:
            self._init_react_chat_prompt_mode()
        elif mode == Mode.REACT_PROMPT:
            self._init_react_prompt_mode()

        self.started = False
        self.llm_chain = LLMChain(
            llm=self.llm, prompt=self.prompt_template, verbose=self.debug
        )
        tool_names = [tool.name for tool in self.tools]
        self.agent = LLMSingleActionAgent(
            llm_chain=self.llm_chain,
            stop=["Tool output:"] if mode == Mode.T5 else ["Observation:"],
            output_parser=self.output_parser,
            allowed_tools=tool_names,
            verbose=self.debug
        )
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=self.visualize_trajectory,
            max_iterations=100,
            max_execution_time=60 * 60,
        )
        self.eval_llm = ChatOpenAI(temperature=0, model_name="gpt-4-0613")
        self.eval_chain = TrajectoryEvalChain.from_llm(
            llm=self.eval_llm,
            agent_tools=self.tools,
            return_reasoning=True
        )

    def _init_t5_mode(self):
        """Initialize T5 mode with specific templates and parsers."""
        with open("src/prompts/T5prompt.txt") as f:
            t5_prompt = f.read()
        self.prompt_template = T5PromptTemplate(
            template=t5_prompt, tools=self.tools, input_variables=["input", "intermediate_steps"]
        )
        self.output_parser = T5OutputParser()

    def _init_travel_mode(self):
        """Initialize travel mode with specific templates and parsers."""
        with open("src/prompts/Travel/make_one_day_itinerary_prompt.txt") as f:
            travel_prompt = f.read()
        self.prompt_template = ReActPromptTemplate(
            template=travel_prompt,
            tools=self.tools,
            input_variables=["famous_sights", "restaurants", "hotel", "intermediate_steps"],
        )
        self.output_parser = ReActOutputParser()

    def _init_react_chat_prompt_mode(self):
        """Initialize ReAct chat mode with specific templates and parsers."""
        with open("src/prompts/ReAct_chat_prompt.txt") as f:
            react_chat_prompt = f.read()
        self.prompt_template = ReActPromptTemplate(
            template=react_chat_prompt, tools=self.tools, input_variables=["input", "intermediate_steps"]
        )
        self.output_parser = ReActOutputParser()

    def _init_react_prompt_mode(self):
        """Initialize ReAct prompt mode with specific templates and parsers."""
        with open("src/prompts/ReAct_prompt.txt") as f:
            react_chat_prompt = f.read()
        self.prompt_template = ReActPromptTemplate(
            template=react_chat_prompt, tools=self.tools, input_variables=["input", "intermediate_steps"]
        )
        self.output_parser = ReActOutputParser()
    
    def kill_agent(self):
        self.agent_executor.killed = True
        self.UI = UI_info()

    def get_intermediate_steps(self):
        return self.agent_executor.intermediate_steps

    def run(self, user_input):
        """Run the agent with given user input and return the results."""
        self.started = True
        return self.agent_executor(inputs=user_input, return_only_outputs=True)
