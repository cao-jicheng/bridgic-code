import os
import time
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.config import project_root
from tools.base import (ToolStatus, ErrorCode, create_success_response, 
    create_partial_response, create_error_response)


DEFAULT_IGNORED_PATTERN = {
    "node_modules",  # Node.js 依赖目录
    "target",        # Java/Scala 构建输出目录
    "build",         # 通用构建输出目录
    "dist",          # 分发目录
    "venv",          # Python 虚拟环境
    "__pycache__",   # Python 字节码缓存
    ".git",          # Git 版本控制目录
    ".svn",          # Subversion 版本控制目录
    ".idea",         # JetBrains IDE 配置目录
    ".vscode",       # VS Code 配置目录
    ".DS_Store",     # macOS 系统文件
    ".venv",         # Python 虚拟环境（另一种命名）
}

def _matches_ignore(name: str, rel_root: str, rel_target: str, patterns: List[str]) -> bool:
    """检查条目是否匹配任一 ignore 模式"""
    for pattern in patterns:
        if "/" in pattern or "\\" in pattern:
            if fnmatch.fnmatch(rel_root, pattern) or fnmatch.fnmatch(rel_target, pattern):
                return True
            if pattern.startswith("**/"):
                if fnmatch.fnmatch(name, pattern[3:]):
                    return True
                if fnmatch.fnmatch(rel_root, pattern[3:]) or fnmatch.fnmatch(rel_target, pattern[3:]):
                    return True
        else:
            if fnmatch.fnmatch(name, pattern):
                return True
    return False

def _symlink_points_to_dir_safe(entry) -> bool:
    """安全检查 symlink 是否指向目录（必须在沙箱内）"""
    try:
        resolved = Path(entry.path).resolve()
        resolved.relative_to(Path(project_root))
        return resolved.is_dir()
    except (ValueError, OSError):
        return False

def _scan_dir(target: Path, include_hidden: bool, ignore: List[str]) -> List[Dict[str, Any]]:
    """扫描目录，应用过滤规则
    Args:
        target: 要扫描的目标目录路径
        include_hidden: 是否包含隐藏文件
        ignore: 要忽略的 glob 模式列表

    Returns:
        包含文件信息的字典列表，每个字典包含 name, type, path, is_dir 键
    """
    items = []
    with os.scandir(target) as it:
        for entry in it:
            name = entry.name
            # 条目相对于 root 的路径（用于 ignore glob 匹配）
            # 注意：不使用 resolve()，保留原始路径，避免 symlink 指向目标路径
            try:
                entry_path_obj = Path(entry.path)
                entry_rel_root = entry_path_obj.relative_to(Path(project_root)).as_posix()
            except Exception:
                entry_rel_root = name
            entry_rel_target = Path(name).as_posix()
            # include_hidden=False 时，跳过隐藏文件和默认忽略列表
            if not include_hidden:
                if name.startswith("."):
                    continue
                if name in DEFAULT_IGNORED_PATTERN:
                    continue
            # 用户自定义 ignore 模式匹配
            if ignore and _matches_ignore(name, entry_rel_root, entry_rel_target, ignore):
                continue
            # 判断是否为链接
            is_symlink = entry.is_symlink()
            # 判断是否为目录
            if is_symlink:
                is_dir = _symlink_points_to_dir_safe(entry)
            else:
                is_dir = entry.is_dir()
            # 确定条目类型
            if is_symlink:
                item_type = "link"
            elif is_dir:
                item_type = "dir"
            else:
                item_type = "file"
            # 条目的相对路径（用于 data.entries）
            entry_path = entry_rel_root
            items.append({
                "name": name,
                "type": item_type,
                "path": entry_path,
                "is_dir": is_dir,
            })
    # 排序：目录在前，文件在后，同类型按名称字母顺序排列
    items.sort(key=lambda x: (0 if x["is_dir"] else 1, x["name"].lower()))
    return items

def _format_response(
    target_path: str,
    total: int,
    dirs_count: int,
    files_count: int,
    links_count: int,
    start: int,
    end: int,
    items: List[dict],
    params_input: Dict[str, Any],
    time_ms: int,
    ) -> str:
    """构建标准化响应，返回的顶层字段仅包含：status, data, text, stats, context"""
    # 判断是否截断
    truncated = end < total
    # 构建 data.entries（对象数组，每项包含 path 和 type）
    entries = [{"path": item["path"], "type": item["type"]} for item in items]
    data = {
        "entries": entries,
        "truncated": truncated,
    }
    # 构建 text（人类可读摘要）
    lines = []
    lines.append(f"列出 {len(entries)} 个实体于目标目录 '{target_path}'")
    lines.append(f"(总计: {total} 个条目 - {dirs_count} 个目录, {files_count} 个文件, {links_count} 条链接)")
    if truncated:
        remaining = total - end
        lines.append(f"[截断: 展示 {start}-{end} 于 {total}, 还剩 {remaining} 个条目可用]")
        lines.append(f"使用 offset={end} 来展示下一页")
    lines.append("")
    for item in items:
        # 显示格式：path + 类型标记
        display = item["path"]
        if item["type"] == "dir":
            display += "/"
        elif item["type"] == "link":
            display += "@"
        lines.append(display)
    text = "\n".join(lines)
    # 构建 extra_stats
    extra_stats = {
        "total_entries": total,
        "dirs": dirs_count,
        "files": files_count,
        "links": links_count,
        "returned": len(entries),
    } 
    # 根据截断状态选择 success 或 partial
    if truncated:
        return create_partial_response(
            data=data,
            text=text,
            params_input=params_input,
            time_ms=time_ms,
            extra_stats=extra_stats,
            target_path=target_path,
        )
    else:
        return create_success_response(
            data=data,
            text=text,
            params_input=params_input,
            time_ms=time_ms,
            extra_stats=extra_stats,
            target_path=target_path,
        )

def list_files(
    path: str=".",
    offset: int=0,
    limit: int=100,
    include_hidden: bool=False,
    ignore: List[str]=[],
    ) -> str:
    """列出文件、目录或链接
    Args:
        path: 要列出的目录路径（默认为 '.'）
        offset: 分页起始索引（默认为 0）
        limit: 返回的最大条目数（默认为 100）
        include_hidden: 是否包含隐藏文件（默认为 False）
        ignore: 要忽略的 glob 模式列表（默认为空）

    Returns:
        JSON 格式的响应字符串
    """
    start_time = time.monotonic()
    # 保存参数列表，用于跟踪调试
    params_input = {
        "path": path,
        "offset": offset,
        "limit": limit,
        "include_hidden": include_hidden,
        "ignore": ignore
    }
    # 参数校验
    if not isinstance(offset, int) or offset < 0:
        return create_error_response(
            error_code=ErrorCode.INVALID_PARAM,
            message="offset 必须是非负整数",
            params_input=params_input,
        )
    if not isinstance(limit, int) or limit < 1 or limit > 200:
        return create_error_response(
            error_code=ErrorCode.INVALID_PARAM,
            message="limit 必须是介于 1 到 200 之间的整数",
            params_input=params_input,
        )
    if not isinstance(ignore, list):
        return create_error_response(
            error_code=ErrorCode.INVALID_PARAM,
            message="ignore 必须是一个包含匹配模式字符串的列表",
            params_input=params_input,
        )
    # 路径解析与沙箱校验
    try:
        target = Path(os.path.abspath(path))
        target_path = target.relative_to(Path(project_root))
    except Exception:
        return create_error_response(
            error_code=ErrorCode.ACCESS_CROSS_BOUND,
            message="访问越界，目标路径不在项目根目录内",
            params_input=params_input,
        )
    # 转换回字符串
    target_path = str(target_path)
    if not target.exists():
        return create_error_response(
            error_code=ErrorCode.NOT_FOUND,
            message=f"目标路径 '{path}' 不存在",
            params_input=params_input,
            target_path=target_path,
        )
    if not target.is_dir():
        return create_error_response(
            error_code=ErrorCode.INVALID_PARAM,
            message=f"目标路径 '{path}' 是一个文件，请用 'Read' 工具查看它的内容",
            params_input=params_input,
            target_path=target_path,
        )
    try:
        items = _scan_dir(target, include_hidden, ignore)
    except PermissionError:
        return create_error_response(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=f"无权限访问目标路径 '{path}'",
            params_input=params_input,
            target_path=target_path,
        )
    except OSError as e:
        return create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=f"列出目录文件失败 - {e}",
            params_input=params_input,
            path_resolved=rel_path,
        )
    # 计算分页范围
    total = len(items)
    start = offset if offset < total else total
    end = min(offset + limit, total)
    page_items = items[start:end]
    # 统计各类条目数量
    dirs_count = sum(1 for t in items if t["type"] == "dir")
    files_count = sum(1 for t in items if t["type"] == "file")
    links_count = sum(1 for t in items if t["type"] == "link")
    # 计算耗时
    time_ms = int((time.monotonic() - start_time) * 1000)
    # 构建响应
    return _format_response(
        target_path=target_path,
        total=total,
        dirs_count=dirs_count,
        files_count=files_count,
        links_count=links_count,
        start=start,
        end=end,
        items=page_items,
        params_input=params_input,
        time_ms=time_ms,
    )
