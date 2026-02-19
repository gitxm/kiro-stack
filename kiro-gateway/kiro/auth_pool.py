# -*- coding: utf-8 -*-

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from kiro.auth import KiroAuthManager


@dataclass
class _Slot:
    idx: int
    manager: KiroAuthManager


@dataclass
class GatewayAuthPool:
    slots: List[_Slot]
    cooldowns: Dict[int, float] = field(default_factory=dict)
    errors: Dict[int, int] = field(default_factory=dict)

    def pick(self) -> Optional[KiroAuthManager]:
        if not self.slots:
            return None

        now = time.time()
        available = [s for s in self.slots if self.cooldowns.get(s.idx, 0) <= now]
        if available:
            return random.choice(available).manager

        # all in cooldown, pick earliest to recover
        best = min(self.slots, key=lambda s: self.cooldowns.get(s.idx, 0))
        return best.manager

    def record_success(self, manager: KiroAuthManager) -> None:
        idx = self._find(manager)
        if idx is None:
            return
        self.errors[idx] = 0
        self.cooldowns.pop(idx, None)

    def record_error(self, manager: KiroAuthManager, status_code: int) -> None:
        idx = self._find(manager)
        if idx is None:
            return
        self.errors[idx] = self.errors.get(idx, 0) + 1

        now = time.time()
        if status_code in (402, 429):
            self.cooldowns[idx] = now + 3600
        elif status_code >= 500 or self.errors[idx] >= 3:
            self.cooldowns[idx] = now + 60

    def _find(self, manager: KiroAuthManager) -> Optional[int]:
        for s in self.slots:
            if s.manager is manager:
                return s.idx
        return None


def build_auth_pool(managers: List[KiroAuthManager]) -> GatewayAuthPool:
    return GatewayAuthPool(slots=[_Slot(idx=i, manager=m) for i, m in enumerate(managers)])
