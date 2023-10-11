import os
import sys

def getRootPath():
    # Get file directory
    curPath = os.path.abspath(os.path.dirname(__file__))
    # Get the root path of the project, containing the current project name
    rootPath = curPath[:curPath.find("Travel/") + len("Travel/")]
    return rootPath

def set_python_path():
    project_path = getRootPath()
    sys.path.append(project_path)
