# -*- coding: utf-8 -*-

def _init():  # 初始化
    global _global_dict
    _global_dict = {}


def set_value(key, value):
    """ 定义一个跨文件全局变量 """
    _global_dict[key] = value

def set_dict_value(key,sub_key,value):
    _global_dict[key][sub_key] = value

def get_value(key):
    try:
        return _global_dict[key]
    except KeyError:
        return 0

def get_dict_value(key, sub_key):
    """ 获得一个跨文件全局变量,不存在则返回默认值 """
    try:
        return _global_dict[key][sub_key]
    except KeyError:
        if key == "wait_user_input":
            return False
        elif key == "chatbot":
            return []
        elif key == "user_inputs":
            return ""
        elif key == "agents":
            return None
        elif key == "travel_plans":
            return ""
        elif key =="user_first_request":
            return ""
        else:
            return 0