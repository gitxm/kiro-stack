<div align="center">

# Kiro Stack

**将 Kiro（Amazon Q Developer）账号转为 OpenAI / Anthropic 兼容 API**

基于 [kiro-gateway](https://github.com/jwadow/kiro-gateway) 与 [Kiro-Go](https://github.com/Quorinex/Kiro-Go) 二次开发

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8?style=flat&logo=go)](https://go.dev/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

</div>

---

## 为什么做这个？

原版项目各有不足：

| | [kiro-gateway](https://github.com/jwadow/kiro-gateway) | [Kiro-Go](https://github.com/Quorinex/Kiro-Go) |
|---|---|---|
| Web 管理面板 | ❌ 无 | ✅ 有 |
| 请求稳定性 | ✅ 强（多重 retry、双端点 fallback） | ⚠️ 一般 |
| 多账号池 | ⚠️ 基础 | ✅ 完善（轮询 + 权重） |
| Token 自动刷新 | ✅ | ✅ |

**本项目将两者结合：**
- **kiro-go** 负责 Web 管理面板 + 账号池管理
- **kiro-gateway** 负责底层 API 调用（重试、双端点 fallback、错误处理）
- kiro-go 检测到 `KIRO_GATEWAY_BASE` 后，自动将请求转发给 kiro-gateway 执行

---

## 架构

```
客户端 (Claude Code / Cursor / Cline ...)
        │
        ▼  :8088
   ┌─────────────┐
   │   kiro-go   │  Web 管理面板 + 账号池 + Token 刷新
   └──────┬──────┘
          │ (内部转发)
          ▼  :8001
   ┌──────────────────┐
   │   kiro-gateway   │  稳定代理层：双端点 fallback + 自动重试
   └──────┬───────────┘
          │
          ▼
      Kiro API (AWS CodeWhisperer / Amazon Q)
```

---

## 快速开始

### 前置条件

- Docker + Docker Compose
- Kiro 账号（免费 / 付费均可）

### 三步启动

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/kiro-stack.git
cd kiro-stack

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改以下两项：
#   ADMIN_PASSWORD=你的管理面板密码
#   INTERNAL_API_KEY=随机生成的密钥（用于内部通信）

# 3. 启动服务
docker compose up -d
```

### 添加账号并使用

1. 打开 `http://localhost:8088/admin`
2. 使用 `ADMIN_PASSWORD` 登录
3. 添加 Kiro 账号（支持 AWS Builder ID / IAM SSO / SSO Token 等方式）
4. 将客户端的 base URL 设为 `http://localhost:8088`

```bash
# OpenAI 兼容
curl http://localhost:8088/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4.5", "messages": [{"role": "user", "content": "Hello"}]}'

# Anthropic 兼容
curl http://localhost:8088/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4.5", "max_tokens": 1024, "messages": [{"role": "user", "content": "Hello"}]}'
```

> **说明：** 账号凭证由 kiro-go 管理，请求时自动转发给 kiro-gateway，无需在 gateway 单独配置 token。

---

## 支持的模型

模型可用性取决于你的 Kiro 订阅等级，以下为常见模型：

| 模型 | 说明 |
|------|------|
| `claude-sonnet-4.6` | 最新旗舰模型（2026年2月发布） |
| `claude-opus-4.6` | 最强推理模型（2026年2月发布） |
| `claude-sonnet-4.5` | 均衡性能，适合编程、写作等通用任务 |
| `claude-haiku-4.5` | 极速响应，适合简单任务 |
| `claude-sonnet-4` | 上一代，稳定可靠 |
| `claude-3.7-sonnet` | 旧版，向后兼容 |
| `deepseek-v3.2` | 开源 MoE（685B/37B active），均衡 |
| `minimax-m2.1` | 开源 MoE（230B/10B active），适合复杂任务 |
| `qwen3-coder-next` | 开源 MoE（80B/3B active），代码专项 |

模型名称支持多种格式，如 `claude-sonnet-4.5` / `claude-sonnet-4-5` / `claude-sonnet-4-5-20250929` 均可正常解析。

---

## 配置说明

### 环境变量（.env 文件）

所有配置都在根目录的 `.env` 文件中：

| 变量 | 说明 | 必填 |
|------|------|------|
| `ADMIN_PASSWORD` | Web 管理面板密码 | ✅ 是 |
| `INTERNAL_API_KEY` | kiro-go 和 kiro-gateway 之间的通信密钥 | ✅ 是 |
| `VPN_PROXY_URL` | HTTP/SOCKS5 代理（如有网络限制） | ❌ 否 |
| `DEBUG_MODE` | 调试模式：`off`（默认）/ `errors` / `all` | ❌ 否 |

**说明：**
- `ADMIN_PASSWORD`：用于登录 Web 管理面板
- `INTERNAL_API_KEY`：两个服务之间的内部鉴权，随机生成即可（如 `openssl rand -hex 32`）
- `VPN_PROXY_URL`：如果在中国或有网络限制，配置代理地址（如 `http://127.0.0.1:7890`）
- `DEBUG_MODE`：生产环境建议 `off`，排查问题时可设为 `errors`

### 账号管理

所有 Kiro 账号通过 Web 管理面板添加和管理：
1. 访问 `http://localhost:8088/admin`
2. 使用 `ADMIN_PASSWORD` 登录
3. 点击"添加账号"，支持多种方式：
   - AWS Builder ID（个人账号）
   - IAM Identity Center（企业 SSO）
   - SSO Token（从浏览器导入）
   - 本地缓存（从 Kiro IDE 导入）

**无需在 kiro-gateway 配置 token**，所有账号凭证由 kiro-go 管理，请求时自动转发。

---

## 目录结构

```
kiro-stack/
├── docker-compose.yml        # 整合启动配置
├── kiro-gateway/             # Python/FastAPI 稳定代理层
│   ├── kiro/                 # 核心代码
│   ├── requirements.txt
│   └── README.md
├── kiro-go/                  # Go Web 管理面板 + 账号池
│   ├── proxy/                # 核心代理逻辑
│   ├── web/index.html        # 管理面板前端
│   ├── data/
│   │   └── config.example.json  # 配置模板
│   └── README.md
└── scripts/
    └── sync_tokens.py        # Token 同步脚本
```

---

## 更新日志

### 相比原版的改动

**kiro-go 改动：**
- 新增 `KIRO_GATEWAY_BASE` / `KIRO_GATEWAY_API_KEY` 支持，将请求通过 kiro-gateway 中转，大幅提升稳定性
- Web 管理面板优化

**kiro-gateway 改动：**
- 适配与 kiro-go 的联合部署场景

---

## 免责声明

> ⚠️ **请在使用前仔细阅读**

- **账号封禁风险**：使用本项目调用 Kiro API 存在账号被封禁或限流的风险。Kiro / Amazon Q Developer 的服务条款可能不允许此类第三方代理访问，后果由用户自行承担。
- **本项目定位**：本项目仅为对 [kiro-gateway](https://github.com/jwadow/kiro-gateway) 与 [Kiro-Go](https://github.com/Quorinex/Kiro-Go) 的整合与二次开发，**不涉及任何底层请求逻辑的编写**。所有与 Kiro API 的实际通信逻辑均来自上述原始项目。
- **非官方项目**：本项目与 Amazon、AWS、Kiro 官方无任何关联。
- **仅供学习研究**：请勿将本项目用于商业用途或大规模滥用 API。

---

## 致谢

本项目基于以下优秀开源项目二次开发：

- **[kiro-gateway](https://github.com/jwadow/kiro-gateway)** by [@Jwadow](https://github.com/jwadow) — AGPL-3.0
- **[Kiro-Go](https://github.com/Quorinex/Kiro-Go)** by [@Quorinex](https://github.com/Quorinex) — MIT

---

## 许可证

本项目遵循各子项目原有许可证：
- `kiro-gateway/` — [AGPL-3.0](kiro-gateway/LICENSE)
- `kiro-go/` — [MIT](kiro-go/LICENSE) *(如原项目有)*

整合部分代码遵循 MIT 许可证。
