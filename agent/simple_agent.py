from typing import Optional
from bridgic.core.agentic.tool_specs import FunctionToolSpec
from bridgic.core.automa import RunningOptions
from bridgic.core.agentic.recent import ReCentAutoma, ReCentMemoryConfig, StopCondition
from core.llm import chat_llm
from tools import list_files

# 将各个工具函数转换为 Bridgic 的 FunctionToolSpec
funcs = [list_files]
tools_list = [FunctionToolSpec.from_raw(fn) for fn in funcs]

async def SimpleAgent(goal: str, guidance: Optional[str]=None, debug: bool=False) -> None:
    agent = ReCentAutoma(
        llm=chat_llm,
        tools=tools_list,
        memory_config=ReCentMemoryConfig(
            llm=chat_llm,
            max_node_size=20,
            max_token_size=1024*128,
        ),
        stop_condition=StopCondition(max_iteration=20, max_consecutive_no_tool_selected=1),
        running_options=RunningOptions(debug=debug)
    )
    final_guidance = guidance if guidance else "请选择合适的工具来执行"
    result = await agent.arun(goal=goal, guidance=final_guidance)
    print(f"最终结果为：\n{result}")


if __name__ == "__main__":
    import asyncio

    goal = "列出 ./core 目录里面的文件"
    guidance = "请选择 `list_files` 工具来执行"

    asyncio.run(SimpleAgent(goal=goal, guidance=guidance, debug=True))