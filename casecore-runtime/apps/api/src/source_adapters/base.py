from abc import ABC, abstractmethod


class SourceAdapter(ABC):
    source_class: str

    @abstractmethod
    def retrieve(self, query: str, filters: dict, jurisdiction: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def classify(self, raw_item: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, classified_item: dict) -> dict:
        raise NotImplementedError
