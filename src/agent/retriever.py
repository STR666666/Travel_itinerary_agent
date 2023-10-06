import src.tools.travel.general_agent_chat as trip_chat
import src.tools.travel.modify_itinerary as modify_itinerary
from typing import List, Dict, Any

def extract_function_names(file_path: str) -> List[str]:
    """
    Extracts function names from a given Python file.

    Parameters:
    - file_path : str : The path to the Python file.

    Returns:
    - List[str] : A list of function names defined in the file.
    """
    function_names = []
    
    with open(file_path, encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith("def ") and not line[4] == "_":
            function_name = line[4:].split("(")[0].strip()
            function_names.append(function_name)
    
    return function_names

class ToolRetriever:
    """
    A class to retrieve APIs that are defined in a Python file.
    """

    def __init__(self, tool_path: str):
        """
        Initializes the ToolRetriever with the given tool path.

        Parameters:
        - tool_path : str : The path of the tool file relative to the 'src/tools/' directory.
        """
        self.tools = self._load_tools("src/tools/" + tool_path)
        self.name_to_module: Dict[str, Any] = {
            "travel/general_agent_chat.py": trip_chat,
            "travel/modify_itinerary.py": modify_itinerary
        }

    def _load_tools(self, full_tool_path: str) -> List[Any]:
        """
        Loads tools from the specified tool file.

        Parameters:
        - full_tool_path : str : The full path of the tool file.

        Returns:
        - List[Any] : A list of tools loaded from the file.
        """
        tool_names = extract_function_names(full_tool_path)
        module = self.name_to_module.get(full_tool_path.split('/')[-1])

        if not module:
            raise ImportError(f"No module found for the path {full_tool_path}")

        return [getattr(module, tool_name) for tool_name in tool_names]

    def get_tools(self) -> List[Any]:
        """
        Returns the loaded tools.

        Returns:
        - List[Any] : A list of loaded tools.
        """
        return self.tools