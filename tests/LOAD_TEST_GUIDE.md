# RAGFlow-Plus 并发压力测试指南

## 1. 安装 Locust

```bash
pip install locust
```

## 2. 获取 Authorization Token

1. 登录系统后，打开浏览器开发者工具（F12）
2. 切换到 **Application** 标签页
3. 在左侧 **Local Storage** 中找到 `Authorization` 的值
4. 复制该值（格式类似：`IjVhMzMxOGUwZWExMDExZjA5NmZjZmExNjNlZDRlMzg1Ig.aVt16A.s8IPNLUBt25MIOnhdHpDRywsH2M`）

## 3. 配置测试脚本

编辑 `tests/locustfile.py`，将以下位置替换为你的实际值：

```python
# 第 38 行
self.token = "YOUR_AUTHORIZATION_TOKEN"  # 替换为你的 token

# 第 74 行
dialog_id = "d6e28af6bbb3460882d5e9f317ee0af0"  # 替换为实际对话 ID
```

## 4. 运行测试

### 方式一：Web UI 模式（推荐）

```bash
cd /home/mss/data/ragflow-plus/tests
locust -f locustfile.py --host=http://10.86.100.39
```

然后打开浏览器访问 **http://localhost:8089**：

1. **Number of users**：总并发用户数（如 100）
2. **Spawn rate**：每秒启动用户数（如 10）
3. 点击 **Start swarming** 开始测试

### 方式二：命令行模式（无 UI）

```bash
# 100 用户，每秒启动 10 个，运行 60 秒
locust -f locustfile.py \
    --host=http://10.86.100.39 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --headless
```

### 方式三：只测试特定用户类

```bash
# 只测试普通用户行为
locust -f locustfile.py --host=http://10.86.100.39 RAGFlowUser

# 只测试聊天功能
locust -f locustfile.py --host=http://10.86.100.39 ChatUser
```

## 5. 测试指标说明

| 指标 | 说明 |
|------|------|
| **RPS** | 每秒请求数 |
| **Response time (ms)** | 响应时间（中位数、95%、99%） |
| **Failures** | 失败请求数 |
| **Users** | 当前并发用户数 |

## 6. 建议的测试场景

### 场景一：基准测试
- 用户数：50
- 持续时间：5 分钟
- 预期：了解系统基准性能

### 场景二：正常负载
- 用户数：100
- 持续时间：10 分钟
- 预期：模拟正常使用情况

### 场景三：压力测试
- 用户数：200-500
- 持续时间：15 分钟
- 预期：找出系统瓶颈

### 场景四：峰值测试
- 用户数：从 10 快速增加到 300
- 持续时间：5 分钟
- 预期：测试系统应对突发流量能力

## 7. 导出测试报告

```bash
# 生成 HTML 报告
locust -f locustfile.py \
    --host=http://10.86.100.39 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 60s \
    --headless \
    --html=report.html
```

## 8. 常见问题

### Q: 测试时出现大量 401 错误？
A: Token 已过期，需要重新登录获取新的 token。

### Q: 响应时间过长？
A: 可能的原因：
- 数据库连接池不够
- 后端 worker 数量不足
- 网络带宽限制

### Q: 如何测试聊天 API？
A: 聊天涉及大模型调用，响应时间较长，建议单独测试，并发数不宜过高。
