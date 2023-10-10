import os
import sys
def getRootPath():
    # 获取文件目录
    curPath = os.path.abspath(os.path.dirname(__file__))
    # 获取项目根路径，内容为当前项目的名字
    rootPath = curPath[:curPath.find("Travel/")+len("Travel/")]
    return rootPath

def set_python_path():
    project_path = getRootPath()
    sys.path.append(project_path)