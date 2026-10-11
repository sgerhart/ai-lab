"""A personal follow-up can see earlier lines in the same chat."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.agent_loop import earlier_turns  # noqa: E402
from ai_lab_platform.agent_worker import drain_queued_runs  # noqa: E402
from ai_lab_platform.conversation import (  # noqa: E402
    AgentRun,
    AgentRunStatus,
    BillingClass,
    Conversation,
    Message,
    MessageRole,
    RunBudget,
)
from ai_lab_platform.model_router import CompletionResponse, ModelRouter  # noqa: E402
from ai_lab_platform.store import SqliteStore  # noqa: E402


class _RecordingBackend:
    billing_class = BillingClass.LOCAL

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, request) -> CompletionResponse:
        self.prompts.append(request.prompt)
        return CompletionResponse(
            model=request.model,
            backend="scripted",
            text="FINAL ok",
            billing_class=self.billing_class,
        )


class EarlierTurnTests(unittest.TestCase):
    def test_current_question_is_not_repeated(self) -> None:
        messages = [
            Message.new(conversation_id="c", role=MessageRole.USER, content="The suitcase is blue."),
            Message.new(conversation_id="c", role=MessageRole.ASSISTANT, content="I noted that."),
            Message.new(conversation_id="c", role=MessageRole.USER, content="What color is the suitcase?"),
        ]
        text = earlier_turns(messages, "What color is the suitcase?")
        self.assertIn("user: The suitcase is blue.", text)
        self.assertIn("assistant: I noted that.", text)
        self.assertNotIn("What color", text)

    def test_only_the_current_line_leaves_history_empty(self) -> None:
        messages = [
            Message.new(conversation_id="c", role=MessageRole.USER, content="hello"),
        ]
        self.assertEqual(earlier_turns(messages, "hello"), "")

    def test_keeps_the_latest_lines_only(self) -> None:
        messages = [
            Message.new(conversation_id="c", role=MessageRole.USER, content=f"line {index}")
            for index in range(12)
        ]
        text = earlier_turns(messages, "line 11")
        self.assertNotIn("line 0", text)
        self.assertIn("line 3", text)
        self.assertNotIn("line 11", text)


class PersonalFollowUpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SqliteStore(Path(self.tmp.name) / "wo.sqlite")
        self.backend = _RecordingBackend()
        self.router = ModelRouter(backends={"scripted": self.backend})
        self._env = os.environ.get("AI_LAB_MEMORY_VAULT")
        os.environ["AI_LAB_MEMORY_VAULT"] = str(Path(self.tmp.name) / "memory")

    def tearDown(self) -> None:
        if self._env is None:
            os.environ.pop("AI_LAB_MEMORY_VAULT", None)
        else:
            os.environ["AI_LAB_MEMORY_VAULT"] = self._env
        self.tmp.cleanup()

    def _queue(self, agent: str, objective: str, conversation_id: str) -> None:
        run = AgentRun.new(
            agent=agent,
            objective=objective,
            conversation_id=conversation_id,
            model="scripted",
            billing_class=BillingClass.LOCAL,
            backend="scripted",
            budget=RunBudget(max_steps=4),
        )
        run.status = AgentRunStatus.QUEUED
        self.store.put_agent_run(run)

    def test_personal_follow_up_sees_the_earlier_answer(self) -> None:
        conv = Conversation.new(agent="personal", title="Day")
        self.store.put_conversation(conv)
        self.store.put_message(
            Message.new(conversation_id=conv.id, role=MessageRole.USER, content="The suitcase is blue.")
        )
        self.store.put_message(
            Message.new(
                conversation_id=conv.id,
                role=MessageRole.ASSISTANT,
                content="I noted that.",
                meta={"kind": "personal_reply"},
            )
        )
        self.store.put_message(
            Message.new(
                conversation_id=conv.id,
                role=MessageRole.USER,
                content="What color is the suitcase?",
            )
        )
        self._queue("personal", "What color is the suitcase?", conv.id)
        drain_queued_runs(self.store, self.router, limit=1)
        self.assertTrue(self.backend.prompts)
        prompt = self.backend.prompts[0]
        self.assertIn("Earlier in this conversation:", prompt)
        self.assertIn("The suitcase is blue.", prompt)
        self.assertIn("Current question:\nWhat color is the suitcase?", prompt)

    def test_lab_run_does_not_receive_chat_history(self) -> None:
        conv = Conversation.new(agent="lab-operations", title="Health")
        self.store.put_conversation(conv)
        self.store.put_message(
            Message.new(conversation_id=conv.id, role=MessageRole.USER, content="The suitcase is blue.")
        )
        self._queue("lab-operations", "check health", conv.id)
        drain_queued_runs(self.store, self.router, limit=1)
        self.assertTrue(self.backend.prompts)
        self.assertNotIn("Earlier in this conversation:", self.backend.prompts[0])
        self.assertNotIn("suitcase", self.backend.prompts[0])
