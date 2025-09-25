from dataclasses import dataclass
from typing import Optional
from environs import Env


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig


def load_config(path: Optional[str] = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=env.list("ADMIN_IDS", subcast=int),
        ),
        db=DatabaseConfig(
            url=env.str("DATABASE_URL"),
        )
    )
