import os
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import project_root

class ToolStatus(str, Enum):
    """工具运行状态枚举
    - SUCCESS: 任务完全按预期执行，无截断、无回退、无错误
    - PARTIAL: 结果可用但有折损（截断/回退/部分失败）
    - ERROR: 无法提供有效结果（致命错误）
    """
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"

class ErrorCode(str, Enum):
    """标准错误码枚举"""
    NOT_FOUND = "not_found"                        # 文件/路径不存在
    ACCESS_CROSS_BOUND = "access_cross_bound"      # 路径不在工作区目录内（沙箱越界）
    PERMISSION_DENIED = "permission_denied"        # 访问权限不足（EACCES 等）
    INVALID_PARAM = "invalid_param"                # 参数校验失败（正则错误、类型错误等）
    TIMEOUT = "timeout"                            # 工具运行超时
    INTERNAL_ERROR = "internal_error"              # 未分类的内部异常
    EXECUTION_ERROR = "execution_error"            # 其它 I/O 或执行错误（磁盘满等）
    IS_DIRECTORY = "is_directory"                  # 路径是目录而非文件
    BINARY_FILE = "binary_file"                    # 文件是二进制格式
    CONFLICT = "conflict"                          # 文件在读取后被修改（访问锁冲突）
    CIRCUIT_OPEN = "circuit_open"                  # 工具熔断中（临时禁用）
    ASK_USER_UNAVAILABLE = "ask_user_unavailable"  # 子代理禁止交互
    MCP_PARAM_ERROR = "mcp_param_error"            # MCP 参数错误
    MCP_PARSE_ERROR = "mcp_parse_error"            # MCP 解析错误
    MCP_EXECUTION_ERROR = "mcp_execution_error"    # MCP 执行错误
    MCP_NETWORK_ERROR = "mcp_network_error"        # MCP 网络错误
    MCP_TIMEOUT = "mcp_timeout"                    # MCP 访问超时
    MCP_NOT_FOUND = "mcp_not_found"                # MCP 工具不存在

def _get_relative_cwd() -> str:
    current = Path(os.getcwd())
    try:
        rel_cwd = current.relative_to(Path(project_root))
        return str(rel_cwd)
    except Exception:
        return '.'

def _build_response(
    status: ToolStatus,
    data: Dict[str, Any],
    text: str,
    params_input: Dict[str, Any],
    time_ms: int,
    target_path: Optional[str] = None,
    extra_stats: Optional[Dict[str, Any]] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    ) -> str:
    """内部方法：构建标准响应信封
    返回字段严格限制为：status, data, text, stats, context
    （error 仅在 status="error" 时由 create_error_response 添加）
    """
    context: Dict[str, Any] = {
        "cwd": _get_relative_cwd(),
        "params_input": params_input,
    }
    if target_path is not None:
        context["target_path"] = target_path
    if extra_context:
        context.update(extra_context)
    try:
        time_ms = int(time_ms)
    except Exception:
        time_ms = 0
    if status != ToolStatus.ERROR and time_ms <= 0:
        time_ms = 1
    stats: Dict[str, Any] = {"time_ms": time_ms}
    if extra_stats:
        stats.update(extra_stats)
    payload = {
        "status": status.value,
        "data": data,
        "text": text,
        "stats": stats,
        "context": context,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

def create_success_response(
    data: Dict[str, Any],
    text: str,
    params_input: Dict[str, Any],
    time_ms: int,
    target_path: Optional[str] = None,
    extra_stats: Optional[Dict[str, Any]] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    ) -> str:
    """创建成功响应（status="success"），适用于任务完全按预期执行、无截断、无回退的场景。
    Args:
        data: 核心载荷（必须是对象，不允许 null）
        text: 给 LLM 阅读的格式化摘要
        params_input: 调用时传入的原始参数
        time_ms: 工具执行耗时（毫秒）
        target_path: 目标路径（如果涉及路径解析）
        extra_stats: 额外的统计字段
        extra_context: 额外的上下文字段
            
    Returns:
        JSON 格式的响应字符串
    """
    return _build_response(status=ToolStatus.SUCCESS, data=data, text=text, params_input=params_input,
        time_ms=time_ms, target_path=target_path, extra_stats=extra_stats, extra_context=extra_context)

def create_partial_response(
    data: Dict[str, Any],
    text: str,
    params_input: Dict[str, Any],
    time_ms: int,
    target_path: Optional[str] = None,
    extra_stats: Optional[Dict[str, Any]] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    ) -> str:
    """创建部分成功响应（status="partial"），适用于结果可用但有"折扣"的场景：截断、回退、部分失败等。
    Args:
        data: 核心载荷（应包含 truncated/fallback 等标记说明原因。）
        text: 给 LLM 阅读的格式化摘要（应说明折扣原因和下一步建议）
        params_input: 调用时传入的原始参数
        time_ms: 工具执行耗时（毫秒）
        target_path: 目标路径（如果涉及路径解析）
        extra_stats: 额外的统计字段
        extra_context: 额外的上下文字段
            
    Returns:
        JSON 格式的响应字符串
    """
    return _build_response(status=ToolStatus.PARTIAL, data=data, text=text, params_input=params_input,
        time_ms=time_ms, target_path=target_path, extra_stats=extra_stats, extra_context=extra_context)

def create_error_response(
    error_code: ErrorCode,
    message: str,
    params_input: Dict[str, Any],
    time_ms: int = 0,
    data: Optional[Dict[str, Any]] = None,
    target_path: Optional[str] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    ) -> str:
    """创建错误响应（status="error"），适用于工具无法提供有效结果的场景。
    Args:
        error_code: 标准错误码（仅在此情况下存在）
        message: 人类可读的错误消息
        params_input: 调用时传入的原始参数
        time_ms: 工具执行耗时（毫秒）
        target_path: 目标路径（如果涉及路径解析）
        extra_context: 额外的上下文字段
            
    Returns:
        JSON 格式的响应字符串
    """
    context: Dict[str, Any] = {
        "cwd": _get_relative_cwd(),
        "params_input": params_input,
    }
    if target_path is not None:
        context["target_path"] = target_path
    if extra_context:
        context.update(extra_context)
        
    stats: Dict[str, Any] = {"time_ms": time_ms}
    error_data: Dict[str, Any] = data or {}
    payload = {
        "status": ToolStatus.ERROR.value,
        "data": error_data,
        "text": message,
        "error": {
            "code": error_code.value,
            "message": message,
        },
        "stats": stats,
        "context": context,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
