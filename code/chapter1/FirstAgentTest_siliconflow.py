# -*- coding: UTF-8 -*-
# @Project      ：hello-agents
# @IDE          ：PyCharm
# @Author       ：Devin
# @Description  ：FirstAgentTest_siliconflow.py
# @Date         ：2026/4/9 13:48
AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 行动格式:
你的回答必须严格遵循以下格式。首先是你的思考过程，然后是你要执行的具体行动。
Thought: [这里是你的思考过程和下一步计划]
Action: [这里是你要调用的工具，格式为 function_name(arg_name="arg_value")]

# 任务完成:
当你收集到足够的信息，能够回答用户的最终问题时，你必须使用 `finish(answer="...")` 来输出最终答案。

请开始吧！
"""

import requests
import json
import os
import re
from tavily import TavilyClient
from openai import OpenAI


def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    """
    url = f"https://wttr.in/{city}?format=j1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"

    except requests.exceptions.RequestException as e:
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """
    api_key = os.environ.get("TAVILY_API_KEY")

    if not api_key:
        return "错误：未配置TAVILY_API_KEY。"

    tavily = TavilyClient(api_key=api_key)
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        response = tavily.search(query=query, search_depth="basic", include_answer=True)

        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题 - {e}"


# 将所有工具函数放入一个字典
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}


class SiliconFlowClient:
    """
    专门用于调用 SiliconFlow API 的客户端，支持流式输出。
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用 SiliconFlow API 来生成回应，支持流式输出。"""
        print("正在调用大语言模型...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]

            # 使用流式输出
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True  # 启用流式输出
            )

            # 收集完整的响应内容
            full_content = ""
            print("模型响应: ", end="", flush=True)

            for chunk in response:
                if not chunk.choices:
                    continue

                # 处理普通内容
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_content += content

                # 如果是推理模型（如 DeepSeek-R1），处理推理内容
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    reasoning = chunk.choices[0].delta.reasoning_content
                    print(f"\n[推理过程: {reasoning}]", end="", flush=True)

            print("\n大语言模型响应成功。")
            return full_content

        except Exception as e:
            print(f"\n调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"


# --- 1. 配置LLM客户端 ---
# 使用 SiliconFlow 的配置
API_KEY = "******************************"
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL_ID = "Qwen/Qwen2.5-72B-Instruct"  # 或者使用 "Pro/deepseek-ai/DeepSeek-R1"
os.environ['TAVILY_API_KEY'] = "YOUR_TAVILY_API_KEY"

llm = SiliconFlowClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)

# --- 2. 初始化 ---
user_prompt = "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
prompt_history = [f"用户请求: {user_prompt}"]

print(f"用户输入: {user_prompt}\n" + "=" * 40)

# --- 3. 运行主循环 ---
for i in range(5):  # 设置最大循环次数
    print(f"\n--- 循环 {i + 1} ---\n")

    # 3.1. 构建Prompt
    full_prompt = "\n".join(prompt_history)

    # 3.2. 调用LLM进行思考
    llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
    print(f"\n\n完整模型输出:\n{llm_output}\n")
    prompt_history.append(llm_output)

    # 3.3. 解析并执行行动
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
    if not action_match:
        print("解析错误：模型输出中未找到 Action。")
        break
    action_str = action_match.group(1).strip()

    if action_str.startswith("finish"):
        final_answer = re.search(r'finish\(answer="(.*)"\)', action_str, re.DOTALL)
        if final_answer:
            final_answer = final_answer.group(1)
        else:
            final_answer = action_str
        print(f"任务完成，最终答案: {final_answer}")
        break

    tool_match = re.search(r"(\w+)\(", action_str)
    if not tool_match:
        print("解析错误：无法识别工具名称。")
        break

    tool_name = tool_match.group(1)
    args_str = re.search(r"\((.*)\)", action_str, re.DOTALL)
    if args_str:
        args_str = args_str.group(1)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))
    else:
        kwargs = {}

    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"错误：未定义的工具 '{tool_name}'"

    # 3.4. 记录观察结果
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "=" * 40)
    prompt_history.append(observation_str)