#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConversationState:
    turns: List[Dict[str, str]] = field(default_factory=list)

    def add_turn(self, query: str, context: str, answer: str) -> None:
        self.turns.append({"query": query, "context": context, "answer": answer})
        self.turns = self.turns[-8:]

    def merged_context(self) -> str:
        return "\n".join(
            f"Q: {turn['query']}\nContext: {turn['context']}\nA: {turn['answer']}"
            for turn in self.turns
        )

