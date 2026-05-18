"""Alibaba Cloud DNS MCP Server

Low-level MCP Server implementation for managing Alibaba Cloud DNS records.
"""

import os
import logging
from typing import Any

import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from alibabacloud_alidns20150109.client import Client as AlidnsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alidns20150109 import models as alidns_models

logger = logging.getLogger(__name__)

server = Server("alidns")


def _get_client() -> AlidnsClient:
    ak_id = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
    ak_secret = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    if not ak_id or not ak_secret:
        raise RuntimeError(
            "ALIBABA_CLOUD_ACCESS_KEY_ID and "
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET must be set"
        )
    config = open_api_models.Config(
        access_key_id=ak_id,
        access_key_secret=ak_secret,
    )
    config.endpoint = "alidns.cn-hangzhou.aliyuncs.com"
    return AlidnsClient(config)


# ──────────────────────────────────────────────
# Tool handlers
# ──────────────────────────────────────────────


def _list_domains(keyword: str | None = None) -> str:
    client = _get_client()
    req = alidns_models.DescribeDomainsRequest()
    if keyword:
        req.key_word = keyword
    try:
        resp = client.describe_domains(req)
        domains = resp.body.domains.domain if resp.body.domains else []
        if not domains:
            return "没有找到域名"
        lines = [f"共 {resp.body.total_count} 个域名："]
        for d in domains:
            lines.append(
                f"  · {d.domain_name}  (ID: {d.domain_id})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"查询失败：{e}"


def _list_records(
    domain_name: str, page_number: int = 1, page_size: int = 20
) -> str:
    client = _get_client()
    req = alidns_models.DescribeDomainRecordsRequest(
        domain_name=domain_name,
        page_number=page_number,
        page_size=page_size,
    )
    try:
        resp = client.describe_domain_records(req)
        records = resp.body.domain_records.record if resp.body.domain_records else []
        if not records:
            return f"「{domain_name}」没有找到解析记录"
        lines = [
            f"「{domain_name}」解析记录"
            f"（共 {resp.body.total_count} 条）："
        ]
        for r in records:
            lines.append(
                f"  [{r.record_id}] {r.rr} {r.type} → {r.value}  "
                f"(TTL: {r.ttl}, 状态: {r.status})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"查询失败：{e}"


def _add_record(
    domain_name: str,
    rr: str,
    record_type: str,
    value: str,
    ttl: int = 600,
    priority: int | None = None,
    line: str | None = None,
) -> str:
    client = _get_client()
    req = alidns_models.AddDomainRecordRequest(
        domain_name=domain_name,
        rr=rr,
        type=record_type,
        value=value,
        ttl=ttl,
        line=line or "default",
    )
    if priority is not None:
        req.priority = priority
    try:
        resp = client.add_domain_record(req)
        return f"添加成功！RecordID: {resp.body.record_id}"
    except Exception as e:
        return f"添加失败：{e}"


def _update_record(
    record_id: str,
    rr: str,
    record_type: str,
    value: str,
    ttl: int = 600,
    priority: int | None = None,
    line: str | None = None,
) -> str:
    client = _get_client()
    req = alidns_models.UpdateDomainRecordRequest(
        record_id=record_id,
        rr=rr,
        type=record_type,
        value=value,
        ttl=ttl,
        line=line or "default",
    )
    if priority is not None:
        req.priority = priority
    try:
        client.update_domain_record(req)
        return f"更新成功！RecordID: {record_id}"
    except Exception as e:
        return f"更新失败：{e}"


def _delete_record(record_id: str) -> str:
    client = _get_client()
    req = alidns_models.DeleteDomainRecordRequest(record_id=record_id)
    try:
        client.delete_domain_record(req)
        return f"删除成功！RecordID: {record_id}"
    except Exception as e:
        return f"删除失败：{e}"


# ──────────────────────────────────────────────
# MCP registration
# ──────────────────────────────────────────────


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_domains",
            description="列出阿里云 DNS 域名列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "按关键词搜索域名（可选）",
                    }
                },
            },
        ),
        types.Tool(
            name="list_records",
            description="获取指定域名的 DNS 解析记录列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain_name": {
                        "type": "string",
                        "description": "域名，如 example.com",
                    },
                    "page_number": {
                        "type": "integer",
                        "description": "页码，默认为 1",
                        "default": 1,
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "每页条数，默认为 20",
                        "default": 20,
                    },
                },
                "required": ["domain_name"],
            },
        ),
        types.Tool(
            name="add_record",
            description="添加 DNS 解析记录",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain_name": {
                        "type": "string",
                        "description": "域名，如 example.com",
                    },
                    "rr": {
                        "type": "string",
                        "description": "主机记录，如 @, www, api",
                    },
                    "record_type": {
                        "type": "string",
                        "description": "记录类型，如 A, CNAME, MX, TXT, AAAA",
                    },
                    "value": {
                        "type": "string",
                        "description": "记录值",
                    },
                    "ttl": {
                        "type": "integer",
                        "description": "TTL（秒），默认 600",
                        "default": 600,
                    },
                    "priority": {
                        "type": "integer",
                        "description": "MX 优先级（MX 记录必填）",
                    },
                    "line": {
                        "type": "string",
                        "description": "解析线路，默认 default",
                    },
                },
                "required": ["domain_name", "rr", "record_type", "value"],
            },
        ),
        types.Tool(
            name="update_record",
            description="更新 DNS 解析记录",
            inputSchema={
                "type": "object",
                "properties": {
                    "record_id": {
                        "type": "string",
                        "description": "记录 ID",
                    },
                    "rr": {
                        "type": "string",
                        "description": "主机记录",
                    },
                    "record_type": {
                        "type": "string",
                        "description": "记录类型，如 A, CNAME, MX, TXT, AAAA",
                    },
                    "value": {
                        "type": "string",
                        "description": "记录值",
                    },
                    "ttl": {
                        "type": "integer",
                        "description": "TTL（秒），默认 600",
                        "default": 600,
                    },
                    "priority": {
                        "type": "integer",
                        "description": "MX 优先级",
                    },
                    "line": {
                        "type": "string",
                        "description": "解析线路，默认 default",
                    },
                },
                "required": ["record_id", "rr", "record_type", "value"],
            },
        ),
        types.Tool(
            name="delete_record",
            description="删除 DNS 解析记录",
            inputSchema={
                "type": "object",
                "properties": {
                    "record_id": {
                        "type": "string",
                        "description": "记录 ID",
                    },
                },
                "required": ["record_id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    if arguments is None:
        arguments = {}

    handlers = {
        "list_domains": _list_domains,
        "list_records": _list_records,
        "add_record": _add_record,
        "update_record": _update_record,
        "delete_record": _delete_record,
    }

    handler = handlers.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")

    result = handler(**arguments)
    return [types.TextContent(type="text", text=result)]


async def main():
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="alidns-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run():
    """同步入口"""
    import anyio
    anyio.run(main)
