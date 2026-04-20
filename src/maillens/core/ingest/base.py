from abc import ABC, abstractmethod
from typing import Iterator

from maillens.core.models import Message


class Ingester(ABC):
    @abstractmethod
    def iter_messages(self) -> Iterator[Message]:
        ...