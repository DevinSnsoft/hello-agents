"""
ELIZA 聊天机器人实现
==================
ELIZA 是 1966 年由 Joseph Weizenbaum 开发的早期自然语言处理程序，
模拟心理治疗师的对话风格。本程序使用模式匹配和响应模板来实现
简单的对话功能。

核心机制：
1. 模式匹配：使用正则表达式匹配用户输入
2. 响应模板：匹配成功后从预设模板中随机选择回复
3. 代词转换：自动将第一人称和第二人称代词互换

使用方法：
    直接运行脚本，输入文字与机器人对话
    输入 quit/exit/bye 退出程序
"""

import re          # 用于正则表达式模式匹配
import random      # 用于随机选择响应模板

# ============================================
# 规则库：模式(正则表达式) -> 响应模板列表
# ============================================
# 每条规则包含：
#   - 正则表达式模式：用于匹配用户输入
#   - 响应模板列表：匹配成功后随机选择的回复模板
#   - {0} 占位符：将被捕获的用户输入内容替换
# ============================================
rules = {
    r'I need (.*)': [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?"
    ],
    r'Why don\'t you (.*)\?': [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?"
    ],
    r'Why can\'t I (.*)\?': [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?"
    ],
    r'I am (.*)': [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?"
    ],
    r'.* mother .*': [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?"
    ],
    r'.* father .*': [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?"
    ],
    r'.*': [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?"
    ]
}

# ============================================
# 代词转换规则表
# ============================================
# 用于将用户输入中的第一人称转换为第二人称，
# 使机器人的回复听起来像是在回应用户本人。
# 例如：用户说 "I am sad" -> 机器人回复 "Why are you sad?"
# ============================================
pronoun_swap = {
    "i": "you", "you": "i", "me": "you", "my": "your",
    "am": "are", "are": "am", "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will", "yours": "mine",
    "mine": "yours"
}

def swap_pronouns(phrase):
    """
    对输入短语中的代词进行第一/第二人称转换
    
    参数:
        phrase (str): 需要转换的短语，通常是从用户输入中捕获的内容
        
    返回:
        str: 转换后的短语
        
    示例:
        >>> swap_pronouns("I am happy")
        'you are happy'
        >>> swap_pronouns("my father")
        'your father'
    """
    words = phrase.lower().split()                                    # 转为小写并分词
    swapped_words = [pronoun_swap.get(word, word) for word in words]  # 逐个词转换
    return " ".join(swapped_words)                                    # 重新组合成字符串

def respond(user_input):
    """
    根据规则库生成响应
    
    处理流程：
        1. 遍历规则库中的每条规则
        2. 使用正则表达式匹配用户输入（忽略大小写）
        3. 匹配成功时：
           - 提取捕获组内容（括号内的部分）
           - 对捕获内容进行代词转换
           - 随机选择一个响应模板并格式化
        4. 如果没有匹配任何规则，使用通配符规则 r'.*'
    
    参数:
        user_input (str): 用户的原始输入
        
    返回:
        str: 生成的回复文本
    """
    for pattern, responses in rules.items():
        match = re.search(pattern, user_input, re.IGNORECASE)  # 忽略大小写进行匹配
        if match:
            # 捕获匹配到的分组内容（如果有括号捕获组）
            captured_group = match.group(1) if match.groups() else ''
            # 对捕获的文本进行人称代词转换
            swapped_group = swap_pronouns(captured_group)
            # 从响应模板列表中随机选择一个，并将 {0} 替换为处理后的文本
            response = random.choice(responses).format(swapped_group)
            return response
    
    # 如果没有匹配任何特定规则，使用最后的通配符规则（兜底回复）
    return random.choice(rules[r'.*'])

# ============================================
# 主程序入口：交互式聊天循环
# ============================================
if __name__ == '__main__':
    # 打印欢迎语
    print("我是Devin，我在dev_Devin分支进行开发。")
    print("Therapist: Hello! How can I help you today?")
    
    # 无限循环处理用户输入
    while True:
        # 获取用户输入
        user_input = input("You: ")
        
        # 检查是否输入退出命令
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Therapist: Goodbye. It was nice talking to you.")
            break  # 退出循环，结束程序
        
        # 调用 respond 函数生成回复
        response = respond(user_input)
        
        # 打印机器人的回复
        print(f"Therapist: {response}")