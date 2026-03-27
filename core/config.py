import os
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class EnvConfig(BaseModel):
    bc_version: str = Field(
        description="Bridgic Code 版本号"
    )
    project_root: str = Field(
        description="项目根目录"
    )

    @classmethod
    def from_env(cls) -> "EnvConfig":
        return cls(
            bc_version=os.getenv("BC_VERSION", "v0.1.0"),
            project_root=os.getenv("PROJECT_ROOT", "./bridgic-code"),
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
    use_ollama: bool = Field(
        description="是否使用本地 Ollama 模型"
    )
    ollama_model: str = Field(
        description="Ollama 本地模型名称"
    )

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            chat_model=os.getenv("LLM_CHAT_MODEL", "Pro/deepseek-ai/DeepSeek-V3.2"),
            emb_model=os.getenv("LLM_EMB_MODEL", "Qwen/Qwen3-Embedding-0.6B"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1"),
            api_key=os.getenv("LLM_API_KEY", "sk-xxx"),
            use_ollama=(os.getenv("USE_OLLAMA").lower() == "true"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen3.5:27b")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

project_root = os.path.abspath(EnvConfig.from_env().project_root)
