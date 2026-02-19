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

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/kiro-stack.git
cd kiro-stack
```

### 2. 配置 kiro-gateway

```bash
cp kiro-gateway/.env.example kiro-gateway/.env
```

编辑 `kiro-gateway/.env`，至少配置 API Key（用于 kiro-go 调用鉴权）：

```env
# kiro-go 调用时使用的 API Key（自定义，需与 docker-compose.yml 保持一致）
API_KEY=your_api_key_here
```

> 完整配置项参考 [kiro-gateway/README.md](kiro-gateway/README.md)

### 3. 配置 docker-compose.yml

编辑根目录 `docker-compose.yml`：

```yaml
services:
  kiro-gateway:
    ...
    env_file:
      - ./kiro-gateway/.env
    ports:
      - "8001:8000"   # gateway 内部端口，不对外暴露也可

  kiro-go:
    ...
    environment:
      - ADMIN_PASSWORD=your_admin_password   # Web 管理面板密码
      - KIRO_GATEWAY_BASE=http://kiro-gateway:8000
      - KIRO_GATEWAY_API_KEY=your_api_key_here   # 需与 gateway API_KEY 一致
    ports:
      - "8088:8080"   # 对外暴露端口
```

### 4. 启动服务

```bash
docker compose up -d
```

### 5. 添加账号

1. 打开 `http://localhost:8088/admin`
2. 输入 `ADMIN_PASSWORD` 登录
3. 添加 Kiro 账号（支持 AWS Builder ID / IAM SSO / SSO Token 等方式）

### 6. 使用 API

将客户端的 base URL 设为 `http://localhost:8088`，无需 API Key（或按面板配置）。

```bash
# OpenAI 兼容
curl http://localhost:8088/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4-5", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'

# Anthropic 兼容
curl http://localhost:8088/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4-5", "max_tokens": 1024, "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## 支持的模型

模型可用性取决于你的 Kiro 订阅等级，以下为常见免费模型：

| 模型 | 说明 |
|------|------|
| `claude-sonnet-4-5` | 均衡性能，适合编程、写作等通用任务 |
| `claude-haiku-4-5` | 极速响应，适合简单任务 |
| `claude-sonnet-4` | 上一代，稳定可靠 |
| `claude-3-7-sonnet` | 旧版，向后兼容 |
| `deepseek-v3-2` | 开源 MoE（685B/37B active），均衡 |
| `minimax-m2-1` | 开源 MoE（230B/10B active），适合复杂任务 |
| `qwen3-coder-next` | 开源 MoE（80B/3B active），代码专项 |

模型名称支持多种格式，如 `claude-sonnet-4.5` / `claude-sonnet-4-5` / `claude-sonnet-4-5-20250929` 均可正常解析。

---

## 配置说明

### kiro-go 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `ADMIN_PASSWORD` | Web 管理面板密码 | - |
| `CONFIG_PATH` | 配置文件路径 | `data/config.json` |
| `KIRO_GATEWAY_BASE` | kiro-gateway 地址，设置后请求走 gateway | 空（直连 Kiro API） |
| `KIRO_GATEWAY_API_KEY` | 调用 gateway 的鉴权 Key | 空 |

### kiro-gateway 主要环境变量

详见 [kiro-gateway/README.md](kiro-gateway/README.md)，常用项：

| 变量 | 说明 |
|---|---|
| `API_KEY` | API 访问密钥 |
| `PROXY_URL` | HTTP/SOCKS5 代理（如有网络限制） |
| `MAX_RETRIES` | 最大重试次数 |
| `RETRY_DELAY` | 重试间隔（秒） |

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
