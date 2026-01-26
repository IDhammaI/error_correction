from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

from network_search_agent.prompts import SYSTEM_PROMPT
from network_search_agent.tools import internet_search
# 初始化模型(DeepSeek)
model = init_chat_model(
    model="deepseek:deepseek-chat",
    temperature=0.0
)

# 创建智能体
agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt=SYSTEM_PROMPT,
)
