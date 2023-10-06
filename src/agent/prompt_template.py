import re
from typing import List, Union
from tools.langchain.agents import Tool, AgentOutputParser
from tools.langchain.callbacks.base import BaseCallbackHandler
from tools.langchain.prompts import BaseChatPromptTemplate
from tools.langchain.schema import AgentAction, AgentFinish, HumanMessage
from src.utils import global_value


class StreamPlan(BaseCallbackHandler):
    """Handles the streaming plan for a specific agent."""

    def __init__(self, agent_id: int):
        self.agent_id = agent_id

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Appends new tokens to the travel plans of the specified agent."""
        agent = global_value.get_dict_value('agents', self.agent_id)
        agent.UI_info.travel_plans[-1] += token


class GeneralPromptTemplate(BaseChatPromptTemplate):
    """Constructs a general prompt for the language model."""

    def __init__(self, template: str):
        self.template = template

    def format_messages(self, **kwargs) -> List[HumanMessage]:
        """Formats messages as per the provided template."""
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]


class SpecificPromptTemplate(BaseChatPromptTemplate):
    """Base class for specific types of prompts, e.g., T5 and ReAct."""

    def __init__(self, template: str, tools: List[Tool]):
        self.template = template
        self.tools = tools

    def _format_intermediate_steps(self, intermediate_steps) -> str:
        """To be overridden by subclasses for specific formatting of intermediate steps."""
        pass

    def format_messages(self, **kwargs) -> List[HumanMessage]:
        """Formats messages including intermediate steps and available tools."""
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = self._format_intermediate_steps(intermediate_steps)

        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]


class T5PromptTemplate(SpecificPromptTemplate):
    """Constructs T5 style prompts."""

    def _format_intermediate_steps(self, intermediate_steps) -> str:
        """Formats intermediate steps in T5 style."""
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nTool output: {observation}\nTool reflect: {self._reflection_text()}\nThought:"
        return thoughts

    @staticmethod
    def _reflection_text() -> str:
        """Provides reflection text for the T5 style prompt."""
        return ("1. Do I need an external tool at the current step? If I need a tool, which tool should I call at the current step?\n"
                "2. Which other tools does this tool depend on?\n"
                "3. Remember that I can't generate the final answer until I have called all possible tools to solve the user's problem perfectly.")


class ReActPromptTemplate(SpecificPromptTemplate):
    """Constructs ReAct style prompts."""

    def _format_intermediate_steps(self, intermediate_steps) -> str:
        """Formats intermediate steps in ReAct style."""
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        return thoughts


class SpecificOutputParser(AgentOutputParser):
    """Base class for specific output parsers, to be extended by actual implementations like T5 and ReAct."""

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        """Parses the output of the language model."""
        if "Final Answer:" in llm_output:
            parts = llm_output.split("Final Answer:")
            return AgentFinish(return_values={"output": (parts[0] + parts[1]).strip()}, log=llm_output)

        match = self._get_match(llm_output)
        if not match:
            return AgentAction(tool="None", tool_input="None", log=llm_output)

        tool = match.group(1).strip()
        tool_input = match.group(2).strip(" ").strip('"')
        return AgentAction(tool=tool, tool_input=tool_input, log=llm_output)

    def _get_match(self, llm_output: str):
        """To be overridden by subclasses to provide specific regex matching."""
        pass


class T5OutputParser(SpecificOutputParser):
    """Parses outputs in T5 style."""

    def _get_match(self, llm_output: str):
        """Gets the regex match for T5 style outputs."""
        regex = r"Tool\s*\d*\s*:(.*?)\nTool\s*\d*\s*[iI]nput\s*\d*\s*:[\s]*(.*)"
        return re.search(regex, llm_output, re.DOTALL)


class ReActOutputParser(SpecificOutputParser):
    """Parses outputs in ReAct style."""

    def _get_match(self, llm_output: str):
        """Gets the regex match for ReAct style outputs."""
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*[iI]nput\s*\d*\s*:[\s]*(.*)"
        return re.search(regex, llm_output, re.DOTALL)