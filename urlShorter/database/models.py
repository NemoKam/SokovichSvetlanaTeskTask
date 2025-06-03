"""Модуль хранения таблиц в базе данных."""
from datetime import datetime

from sqlalchemy import DateTime, Index, desc
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовая модель для всех моделей."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), \
                                                 default=lambda: datetime.now(), \
                                                 nullable=False)


class ShortedUrl(Base):
    """Модель хранения укороченных ссылок.

    alias должен соответствовать: [-_0-9a-zA-Z]{4,20}
    original_url должен соответствовать: (http://.{1,2041})|(https://.{1,2040})

    Используемые символы: '-', '_', '0-9', 'a-zA-Z' (длина от 4 до 20 включительно)
    """

    __tablename__ = "shorted_urls"

    original_url: Mapped[str] = mapped_column(nullable=False)
    created_by_ip: Mapped[str] = mapped_column(nullable=True)
    alias: Mapped[str] = mapped_column(nullable=False, unique=True)
    alias_len: Mapped[int] = mapped_column(nullable=False, index=True)
    available_after: Mapped[bool] = mapped_column(default=True)
    clicks: Mapped[int] = mapped_column(default=0)

# Смежный индекс для быстрого поиска
Index("idx_alias_len_and_alias", ShortedUrl.alias_len, ShortedUrl.alias)
# Смежный индекс обратный для поиска ближайшего
Index("idx_alias_len_desc_and_alias_desc",
    desc(ShortedUrl.alias_len),
    desc(ShortedUrl.alias))
