from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from .config import LLMConfig

llm_config = LLMConfig.from_env()

# 设置聊天模型
if llm_config.use_ollama:
    chat_llm = OpenAILlm(
        api_base="http://localhost:11434",
        api_key="no_need",
        configuration=OpenAIConfiguration(model=llm_config.ollama_model),
        timeout=30,
    )
else:
    chat_llm = OpenAILlm(
        api_base=llm_config.base_url,
        api_key=llm_config.api_key,
        configuration=OpenAIConfiguration(model=llm_config.chat_model),
        timeout=30,
    )    
# 设置嵌入模型
emb_llm = OpenAILlm(
    api_base=llm_config.base_url,
    api_key=llm_config.api_key,
    configuration=OpenAIConfiguration(model=llm_config.emb_model),
    timeout=30,
)