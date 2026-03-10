from dataclasses import dataclass
from datetime import datetime


@dataclass
class Movie:
    id: int
    code: str
    message_id: int
    title: str
    added_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "Movie":
        return cls(
            id=data["id"],
            code=data["code"],
            message_id=data["message_id"],
            title=data.get("title", ""),
            added_at=data.get("added_at", ""),
        )


@dataclass
class User:
    id: int
    user_id: int
    username: str
    joined_at: str
