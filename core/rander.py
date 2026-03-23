import os
import random
from typing import Optional, List
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.prompt import Confirm
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.filters import is_done
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter
from core.config import EnvConfig, LLMConfig

logo = \
r""" _               _          
|_)._o _| _ o _ /  _  _| _  
|_)| |(_|(_||(_ \_(_)(_|(/_ 
          _|               """

console = Console()

rander_width = 120

box_style = Style.from_dict({
    "frame.border": "#575557",
    "selected-option": "bold",
    "bottom-toolbar": "#ffffff bg:#333333 noreverse"
})

input_completer = WordCompleter([
    "/init   初始化工作区环境",
    "/models 列出已安装的模型",
    "/tools  列出已安装的工具"
    "/help   显示帮助信息",
])

input_history_path = os.path.expanduser("~/.bridgic-code.input.history")
if not os.path.exists(input_history_path):
    open(input_history_path, 'w').close()

input_session = PromptSession(show_frame=~is_done, history=FileHistory(input_history_path))

def user_confirm(question: str) -> bool:
    return Confirm.ask(question)

def user_choose(options: List[str]) -> str:
    result = choice(
        message="请从下列选项中选择一个：",
        options=[(r, r) for r in options],
        style = box_style, 
        show_frame=~is_done,
        bottom_toolbar=HTML(" 按下 <b>[Up]</b>/<b>[Down]</b> 来选择, <b>[Enter]</b> 来确认")
    )
    return result

def user_input() -> str:
    examples = [
        "统计工作区的文件类型",
        "生成一个快速排序算法",
        "分析当前代码实现了什么功能"
    ]
    result = input_session.prompt("> ", 
        style=box_style,
        completer=input_completer,
        placeholder=f'试一试 "{random.choice(examples)}"',
        bottom_toolbar=HTML(" 支持粘贴单行/多行文本, 按下 <b>[Enter]</b> 来确认")
    )
    return result

def show_banner() -> Panel:
    banner = Table.grid()
    banner.add_row(logo, style="bold red")
    return Panel(banner, border_style="red")

def show_info() -> Panel:
    env = EnvConfig.from_env()
    llm = LLMConfig.from_env()
    info = Table.grid()
    info.add_row(f"[green]当前版本：[/green]{env.version}")
    info.add_row(f"[green]聊天模型：[/green]{llm.chat_model}")
    info.add_row(f"[green]嵌入模型：[/green]{llm.emb_model}")
    info.add_row(f"[green]工作路径：[/green]{env.workspace}")
    return Panel(info, border_style="gray53", width=rander_width-32)

def make_layout() -> Layout:
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="upper", size=6),
        Layout(Panel("暂无进展", title="智能体执行进展", title_align="left", border_style="gray53", width=rander_width), name="progress", minimum_size=3),
        Layout(Panel("暂无输出", title="控制台日志输出", title_align="left", border_style="gray53", width=rander_width), name="progress", minimum_size=3)
    )
    layout["upper"].split_row(
        Layout(name="banner", size=32),
        Layout(name="info")
    )
    layout["banner"].update(show_banner())
    layout["info"].update(show_info())
    return layout



if __name__ == "__main__":
    layout = make_layout()
    console.print(layout)
    user_input()
    user_choose(["小学", "初中", "高中", "大学"])
    user_confirm("是否要继续执行？")
