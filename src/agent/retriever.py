import src.tools.travel.general_agent_chat as trip_chat
import src.tools.travel.modify_itinerary as modify_itinerary
from typing import List, Dict, Any

def extract_function_names(file_path: str) -> List[str]:
    """ Extracts function names from a given Python file. """
    function_names = []
    
    with open(file_path, encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith("def ") and not line[4] == "_":
            function_name = line[4:].split("(")[0].strip()
            function_names.append(function_name)
    
    return function_names

class ToolRetriever:
    """Retrieve APIs that defined in a python file"""
    def __init__(self, tool_path):
        self.tools = []
        tool_names = extract_function_names("src/tools/" + tool_path)
        self.name2py = \
            {
             "travel/general_agent_chat.py": trip_chat,
             "travel/modify_itinerary.py": modify_itinerary}
        for tool_name in tool_names:
            self.tools.append(getattr(self.name2py[tool_path], tool_name))


    def get_tools(self):
        return self.tools