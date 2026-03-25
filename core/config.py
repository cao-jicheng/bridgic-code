import os
from dotenv import load_dotenv
from typing import Dict, List, Any
from pydantic import BaseModel, Field

load_dotenv()

class EnvConfig(BaseModel):
    bc_version: str = Field(
        description="Bridgic Code 版本号"
    )
    workspace: str = Field(
        description="智能体工作区路径"
    )

    @classmethod
    def from_env(cls) -> "EnvConfig":
        return cls(
            bc_version=os.getenv("BC_VERSION", "v0.1.0"),
            workspace=os.getenv("WORKSPACE", "./workspace"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

class LLMConfig(BaseModel):
    chat_model: str = Field(
        description="LLM 聊天模型名称"
    )
    emb_model: str = Field(
        description="LLM 嵌入模型名称"
    )
    base_url: str = Field(
        description="LLM API访问地址"
    )
    api_key: str = Field(
        description="LLM API访问密钥"
    )

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            chat_model=os.getenv("LLM_CHAT_MODEL", "Pro/deepseek-ai/DeepSeek-V3.2"),
            emb_model=os.getenv("LLM_EMB_MODEL", "Qwen/Qwen3-Embedding-0.6B"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
            api_key=os.getenv("LLM_API_KEY", "sk-xxx")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

