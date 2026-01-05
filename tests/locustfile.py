"""
RAGFlow-Plus 并发压力测试脚本
使用 Locust 进行负载测试

使用方法:
1. 安装: pip install locust
2. 运行: locust -f locustfile.py --host=http://10.86.100.39
3. 打开浏览器访问: http://localhost:8089
4. 设置并发用户数和每秒启动用户数，开始测试
"""

from locust import HttpUser, task, between, events
import random
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGFlowUser(HttpUser):
    """模拟普通用户行为"""
    
    # 每个请求之间等待 1-3 秒
    wait_time = between(1, 3)
    
    # 用户的 Authorization token（需要替换为真实 token）
    # 可以通过 CAS 登录后从浏览器开发者工具获取
    token = None
    
    def on_start(self):
        """用户启动时执行，设置认证信息"""
        # 方法1：使用固定 token（从浏览器获取）
        # 替换为你的实际 token
        self.token = "YOUR_AUTHORIZATION_TOKEN"
        
        # 设置请求头
        self.client.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        
        logger.info(f"User started with token: {self.token[:20]}...")
    
    @task(5)  # 权重 5，表示这个任务执行频率最高
    def get_user_info(self):
        """获取用户信息 - 高频接口"""
        with self.client.get("/v1/user/info", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(3)  # 权重 3
    def list_dialogs(self):
        """获取对话列表"""
        with self.client.get("/v1/dialog/list", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)  # 权重 2
    def list_conversations(self):
        """获取会话列表"""
        # 需要一个有效的 dialog_id
        dialog_id = "d6e28af6bbb3460882d5e9f317ee0af0"  # 替换为实际 ID
        with self.client.get(
            f"/v1/conversation/list?dialog_id={dialog_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def get_available_models(self):
        """获取可用模型列表"""
        with self.client.get("/v1/conversation/available_models", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def get_available_kbs(self):
        """获取可用知识库列表"""
        with self.client.get("/v1/conversation/available_kbs", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)  # 权重 1，低频
    def list_knowledge_bases(self):
        """获取知识库列表"""
        with self.client.get("/v1/kb/list", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class ChatUser(HttpUser):
    """模拟对话用户 - 测试聊天功能"""
    
    wait_time = between(5, 10)  # 聊天间隔长一些
    
    token = None
    
    def on_start(self):
        self.token = "YOUR_AUTHORIZATION_TOKEN"
        self.client.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
    
    @task
    def send_chat_message(self):
        """发送对话消息（这是最重要的负载测试）"""
        # 替换为实际的对话 ID
        conversation_id = "YOUR_CONVERSATION_ID"
        
        payload = {
            "conversation_id": conversation_id,
            "messages": [
                {"role": "user", "content": "你好，请介绍一下你自己"}
            ],
            "stream": False  # 非流式，方便测试
        }
        
        with self.client.post(
            "/v1/conversation/completion",
            json=payload,
            catch_response=True,
            timeout=60  # 对话可能需要更长时间
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Chat failed: {response.status_code}")


# 可以选择只运行某一类用户
# 命令行使用: locust -f locustfile.py --host=http://10.86.100.39 --users 100 --spawn-rate 10
