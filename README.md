# alidns-mcp-server

Alibaba Cloud DNS MCP Server — 通过 MCP 协议管理阿里云 DNS 解析记录。

## 功能

| 工具 | 说明 |
|------|------|
| `list_domains` | 列出域名列表 |
| `list_records`  | 查看域名解析记录 |
| `add_record`    | 添加解析记录 |
| `update_record` | 更新解析记录 |
| `delete_record` | 删除解析记录 |

## 前置条件

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv)
- 阿里云 AccessKey（需 DNS 管理权限）

## 配置

### 方式一：Claude Code 全局安装

```bash
claude mcp add-json --scope user alidns-mcp-server \
  '{"command":"uv","args":["run","--directory","/path/to/alidns-mcp-server","alidns-mcp-server"],"env":{"ALIBABA_CLOUD_ACCESS_KEY_ID":"your_key_id","ALIBABA_CLOUD_ACCESS_KEY_SECRET":"your_key_secret"}}'
```

### 方式二：手动编辑 claude.json

在 `~/.claude.json` 的 `mcpServers` 中添加：

```json
{
  "alidns-mcp-server": {
    "command": "uv",
    "args": [
      "run",
      "--directory",
      "/path/to/alidns-mcp-server",
      "alidns-mcp-server"
    ],
    "env": {
      "ALIBABA_CLOUD_ACCESS_KEY_ID": "your_key_id",
      "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "your_key_secret"
    }
  }
}
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | 阿里云 AccessKey ID |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | 阿里云 AccessKey Secret |

AccessKey 可在 [阿里云 RAM 控制台](https://ram.console.aliyun.com/manage/ak) 创建。

## 开发

```bash
git clone git@github.com:Gucvii/alidns-mcp-server.git
cd alidns-mcp-server
uv sync
```

## 用法示例

新开 Claude Code 对话后：

> 列出我的域名
>
> 查看 example.com 的解析记录
>
> 添加一条 A 记录，blog → 1.2.3.4，TTL 600
>
> 删除记录 1234567890

## 技术栈

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Alibaba Cloud DNS SDK for Python](https://github.com/aliyun/alibabacloud-alidns20150109-sdk)
