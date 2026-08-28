"""Agent 间消息总线：实现 Agent 之间的对话协作（CrewAI/AutoGen 风格）。

用户需求：「Agent 间对话协作」——Agent 之间能互相发消息讨论。
例如 Attacker 问 Modeler「这个 cookie 字段什么意思」，
Modeler 回答并补充业务上下文，Attacker 据此调整变异策略。

提供两种通信原语：
  1) direct send：send_to(from_role, to_role, msg) + inbox(role) 取消息
  2) broadcast  ：publish(topic, msg) + 订阅该 topic 的所有 agent 收到

每个 run_id 独立总线，run 结束可清理。线程安全（asyncio 单线程 + lock）。
"""
import asyncio
from collections import defaultdict, deque
from datetime import datetime


class Message:
    """一条 Agent 间消息。"""

    def __init__(self, from_role: str, to_role: str, content: str,
                 topic: str = "", msg_type: str = "chat",
                 round_idx: int = 0):
        self.from_role = from_role
        self.to_role = to_role  # "*" 表示广播
        self.content = content
        self.topic = topic
        self.msg_type = msg_type  # chat / question / answer / broadcast
        self.round_idx = round_idx
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "from": self.from_role, "to": self.to_role,
            "content": self.content, "topic": self.topic,
            "type": self.msg_type, "round": self.round_idx,
            "ts": self.timestamp,
        }

    def __repr__(self) -> str:
        target = self.to_role if self.to_role != "*" else "ALL"
        return (f"[{self.timestamp}] {self.from_role}->{target} "
                f"({self.msg_type}): {self.content[:120]}")


class AgentMessageBus:
    """单个 run 的 Agent 消息总线（进程内、线程安全）。

    用法（在 orchestrator 创建 run 时实例化，传给各 Agent）：
        bus = AgentMessageBus(run_id)
        attacker.bus = bus
        modeler.bus = bus
        # Agent 内部：
        bus.send_to("attacker", "modeler", "cookie 字段 _role 是什么？")
        msgs = bus.inbox("modeler")  # modeler 取走消息
    """

    # 全局 run_id -> bus 映射（便于跨 agent 共享同一总线）
    _buses: dict[str, "AgentMessageBus"] = {}
    _global_lock = asyncio.Lock()

    @classmethod
    async def get_or_create(cls, run_id: str) -> "AgentMessageBus":
        async with cls._global_lock:
            if run_id not in cls._buses:
                cls._buses[run_id] = AgentMessageBus(run_id)
            return cls._buses[run_id]

    @classmethod
    def drop(cls, run_id: str) -> None:
        cls._buses.pop(run_id, None)

    def __init__(self, run_id: str):
        self.run_id = run_id
        self._inbox: dict[str, deque[Message]] = defaultdict(deque)
        self._history: list[Message] = []
        self._subscribers: dict[str, set[str]] = defaultdict(set)  # topic -> roles
        self._lock = asyncio.Lock()

    async def send_to(self, from_role: str, to_role: str, content: str,
                       msg_type: str = "chat", round_idx: int = 0) -> None:
        """点对点发消息（to_role 收件箱追加一条）。"""
        msg = Message(from_role, to_role, content, msg_type=msg_type,
                      round_idx=round_idx)
        async with self._lock:
            self._inbox[to_role].append(msg)
            self._history.append(msg)

    async def publish(self, from_role: str, topic: str, content: str,
                       round_idx: int = 0) -> None:
        """广播到某 topic，订阅该 topic 的所有 role 都收到。"""
        async with self._lock:
            for sub_role in self._subscribers.get(topic, set()):
                msg = Message(from_role, sub_role, content, topic=topic,
                              msg_type="broadcast", round_idx=round_idx)
                self._inbox[sub_role].append(msg)
                self._history.append(msg)

    async def subscribe(self, role: str, topic: str) -> None:
        async with self._lock:
            self._subscribers[topic].add(role)

    async def inbox(self, role: str, peek: bool = False) -> list[Message]:
        """取走 role 收件箱全部消息（peek=True 只看不取）。"""
        async with self._lock:
            msgs = list(self._inbox.get(role, deque()))
            if not peek:
                self._inbox[role].clear()
            return msgs

    async def history(self, role: str = "") -> list[dict]:
        """取历史全部消息（role 留空取全部，否则取涉及该 role 的）。"""
        async with self._lock:
            if not role:
                return [m.to_dict() for m in self._history]
            return [m.to_dict() for m in self._history
                    if m.from_role == role or m.to_role == role
                    or m.to_role == "*"]

    async def ask_and_wait(self, from_role: str, to_role: str,
                            question: str, timeout: float = 5.0,
                            round_idx: int = 0) -> str:
        """同步问答：发问题后阻塞等回复（用于 Agent 主流程中协作调用）。

        注意：要求 to_role 在另一协程中调用 inbox 并 reply。
        MVP 实现：发完问题轮询 inbox 等 answer 类型消息，超时返回空。
        """
        await self.send_to(from_role, to_role, question,
                            msg_type="question", round_idx=round_idx)
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            msgs = await self.inbox(from_role, peek=False)
            for m in msgs:
                if m.msg_type == "answer":
                    return m.content
            await asyncio.sleep(0.2)
        return ""

    async def reply(self, from_role: str, to_role: str, answer: str,
                     round_idx: int = 0) -> None:
        """回复一条 question（写入 to_role 收件箱，type=answer）。"""
        await self.send_to(from_role, to_role, answer,
                           msg_type="answer", round_idx=round_idx)

    def stats(self) -> dict:
        """总线统计（debug 用）。"""
        return {
            "run_id": self.run_id,
            "total_messages": len(self._history),
            "inbox_sizes": {r: len(q) for r, q in self._inbox.items() if q},
            "topics": list(self._subscribers.keys()),
        }
