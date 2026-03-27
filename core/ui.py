import os
import random
from typing import Optional, List, Any
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

box_style = Style.from_dict({
    "frame.border": "#575557",
    "selected-option": "bold",
    "bottom-toolbar": "#ffffff bg:#333333 noreverse"
})

input_examples = [
    "请告诉我应该怎么帮助你？",
    "初始化工程",
    "试一试 “统计工作区的文件类型” ",
    "试一试 “生成一个快速排序算法” ",
    "试一试 “分析当前代码实现了什么功能” "
]

class AgentUI():
    def __init__(self) -> None:
        self.console = Console()
        self.chat_history_path = os.path.expanduser("~/.bridgic-code.chat.history")
        if not os.path.exists(self.chat_history_path):
            open(self.chat_history_path, 'w').close()
        self.input_session = PromptSession(show_frame=~is_done, history=FileHistory(self.chat_history_path))
    
    def print(self, data: Any) -> None:
        return self.console.print(data)

    def user_confirm(self, question: str) -> bool:
        return Confirm.ask(question)

    def user_choose(self, options: List[str]) -> str:
        result = choice(
            message="请从下列选项中选择一个：",
            options=[(r, r) for r in options],
            style = box_style, 
            show_frame=~is_done,
            bottom_toolbar=HTML(" 按下 <b>[Up]</b>/<b>[Down]</b> 来选择, <b>[Enter]</b> 来确认")
        )
        return result

    def user_input(self) -> str:
        result = self.input_session.prompt("> ", 
            style=box_style,
            placeholder=random.choice(input_examples),
            bottom_toolbar=HTML(" 支持粘贴单行/多行文本, 按下 <b>[Enter]</b> 来确认")
        )
        return result.strip()
    
    def clean_chat_history(self) -> None:
        file = open(self.chat_history_path, 'w')
        file.truncate()
        file.close()

    def _show_banner(self) -> Panel:
        banner = Table.grid()
        banner.add_row(logo, style="bold red")
        return Panel(banner, border_style="red")

    def _show_info(self) -> Panel:
        env = EnvConfig.from_env()
        llm = LLMConfig.from_env()
        info = Table.grid()
        info.add_row(f"[green]当前版本：[/green]{env.bc_version}")
        info.add_row(f"[green]聊天模型：[/green]{llm.chat_model}")
        info.add_row(f"[green]嵌入模型：[/green]{llm.emb_model}")
        info.add_row(f"[green]项目路径：[/green]{env.workspace}")
        return Panel(info, border_style="gray53")

    def make_layout(self) -> Layout:
        self.layout = Layout(name="root")
        self.layout.split_column(
            Layout(name="upper", size=6),
            Layout(Panel("暂无进展", title="智能体执行进展", title_align="left", border_style="gray53"), 
                name="progress", minimum_size=3),
            Layout(Panel("暂无输出", title="控制台日志输出", title_align="left", border_style="gray53"), 
                name="output", minimum_size=3)
        )
        self.layout["upper"].split_row(
            Layout(name="banner", size=32),
            Layout(name="info", size=80)
        )
        self.layout["banner"].update(self._show_banner())
        self.layout["info"].update(self._show_info())


if __name__ == "__main__":
    ui = AgentUI()
    ui.make_layout()
    ui.print(ui.layout)
    # ui.user_input()
    # ui.user_choose(["小学", "初中", "高中", "大学"])
    # ui.user_confirm("是否要继续执行？")
    # ui.clean_chat_history()



