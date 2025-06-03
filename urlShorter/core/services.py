"""Модуль сервиса для работы с ссылками."""
import re
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from random import choice, randint

from sqlalchemy import and_, delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import MAX_GET_RANDOM_ALIAS_ATTEMPT_COUNT, MAX_PER_PAGE_URLS_COUNT
from core.exceptions import UnexpectedException
from database.models import ShortedUrl


class AliasNumericService:
    """Сервис для кастомной системы счислений alias'ов."""

    def __init__(self) -> None:
        """Конфигурация сервися кастомной сисетмы счисления alias'ов."""
        # Используемые символы для alias'а:
        self.alias_symbols = ("-0123456789ABCDEFGHIJKLMNOPQRSTU"
                              "VWXYZ_abcdefghijklmnopqrstuvwxyz")
        # Их количество (Вынесено в отдельную переменную для удобства).
        self.symbols_cnt = len(self.alias_symbols)
        # Хранение информации об индексе каждого символа alias'а.
        self.alias_symbols_dict: defaultdict[str, int] = defaultdict(int)

        # Заполняем начиная с 1 для удобства производимых вычислений.
        for i, alias_symbol in enumerate(self.alias_symbols, start=1):
            self.alias_symbols_dict[alias_symbol] = i

    def get_alias_from_alias_numeric(self, alias_numeric: int) -> str:
        """Перевод alias_numeric в alias.

        Args:
            alias_numeric (int): Цифровое значение alias'a.

        Returns:
            str: alias.

        """
        alias = ""

        # Пример работы: alias = "", alias_numeric = 66.
        # 1.1) alias_numeric -= 1 (65)
        # 1.2) alias = "B" + "" ("B")
        # 1.3) alias_numeric //= 64 (1)
        # 2.1) alias_numeric -= 1 (0)
        # 2.2) alias = "A" + "A" ("AB")
        # 2.3) alias_numeric //= 64 (0)
        # Итог: alias_numeric = 66 => alias = "AB".
        while alias_numeric > 0:
            alias_numeric -= 1
            alias = self.alias_symbols[alias_numeric % self.symbols_cnt] + alias
            alias_numeric //= self.symbols_cnt

        return alias

    def get_alias_numeric_from_alias(self, alias: str) -> int:
        """Перевод из alias в alias_numeric.

        Args:
            alias (str): alias.

        Returns:
            int: Цифровое значение alias'а.

        """
        alias_numeric = 0
        multiplier = 1

        # Пример работы: alias = "AB", alias_numeric = 0, multiplier = 1.
        # 1.1) alias_numeric += 2 * 1 (2)
        # 1.2) multiplier *= 64 (64)
        # 2.1) alias_numeric += 1 * 64 (66)
        # 2.2) multiplier *= 64 (4096)
        # Итог: alias = "AB" => alias_numeric = 66.
        for i in range(len(alias) - 1, -1, -1):
            alias_numeric += self.alias_symbols_dict[alias[i]] * multiplier
            multiplier *= self.symbols_cnt

        return alias_numeric


class UrlsService:
    """Сервис для CRUD ссылок."""

    def __init__(self, db: AsyncSession) -> None:
        """Инициализация сервися для CRUD ссылок.

        Args:
            db (AsyncSession): Сессия базы данных.

        """
        self.db: AsyncSession = db
        # Модуль для блокирования процессов выше или ниже алиаса
        # с данным номером взятым по модулю.
        self.alias_numeric_lock_modulo = 2 ** 63
        # Паттерн, которому должен соответствовать алиас.
        self.alias_pattern = "^[-_0-9a-zA-Z]{4,20}$"
        # Паттерн, которому должен соответствовать оригинальный url.
        self.original_url_pattern = "^(http://.{1,2041})|(https://.{1,2040})$"

    async def get_shorted_url_by_alias(self, alias: str) -> ShortedUrl | None:
        """Получение ShortedUrl по его алиасу.

        Args:
            alias (str): Алиас.

        Returns:
            ShortedUrl | None: Возвращает ShortedUrl если алиас есть в базе, иначе None.

        """
        select_shorted_url = select(ShortedUrl).where(ShortedUrl.alias==alias)

        return await self.db.scalar(select_shorted_url)

    async def get_shorted_urls(self, page: int, per_page: int) -> list[ShortedUrl]:
        """Получение списка ShortedUrl с пагинацией.

        Args:
            page (int): Номер страницы.
            per_page (int): Количество ShortedUrl на странице.

        Returns:
            list[ShortedUrl]: Список ShortedUrl

        """
        page = max(1, page) - 1
        per_page = min(MAX_PER_PAGE_URLS_COUNT, per_page)

        select_shorted_urls_stmt = select(ShortedUrl).order_by(
            ShortedUrl.alias_len, ShortedUrl.alias
        ).offset(page * per_page).limit(per_page)
        return list(await self.db.scalars(select_shorted_urls_stmt))

    async def get_ip_shorted_urls_created_count(
        self,
        created_by_ip: str,
        after_time: datetime
    ) -> int:
        """Получение количества созданных shorted_url by ip после указанного времени.

        Args:
            created_by_ip (str): IP адрес пользователя.
            after_time (datetime): Дата и время начала счета.

        Returns:
            int: Количество ShortedUrl.

        """
        select_shorted_urls_created_count_stmt = select(func.count()) \
            .select_from(ShortedUrl).where(and_(
                ShortedUrl.created_by_ip == created_by_ip,
                ShortedUrl.created_at >= after_time
        ))

        result = await self.db.execute(select_shorted_urls_created_count_stmt)
        return result.scalar_one()

    async def get_first_shorted_url_with_available_after(self) -> ShortedUrl | None:
        """Получение первого ShortedUrl с полем available_after=True.

        Returns:
            ShortedUrl | None: Возвращает ShortedUrl если существует подходящая,
            иначе None.

        """
        # Из-за использования index для ShortedUrl.alias order_by
        # должен отрабатывать значительно быстрее
        # ShortedUrl.limit_after != 0 => значение None
        # означает нет лимита => бесконечность.
        select_first_url_stmt = select(ShortedUrl).where(ShortedUrl.available_after) \
            .order_by(ShortedUrl.alias_len, ShortedUrl.alias)

        return await self.db.scalar(select_first_url_stmt)

    async def _lock_by_alias_numeric(self, alias_numeric: int) -> None:
        """Блокировка запросов к Базе Данных по ключу равному alias_numeric по модулю.

        Args:
            alias_numeric (int): Цифровое значение алиаса.

        """
        # Берем по модулю (меньше 2^64) так как, BIGINT не поддерживает больше 2^64.
        remainder_of_division = alias_numeric % self.alias_numeric_lock_modulo
        await self.db.execute(text(
            f"SELECT pg_advisory_xact_lock({remainder_of_division});"))

    async def _get_next_alias_numeric_with_lock(self) -> int:
        """Нахождение первого свободного alias_numeric и блокирование с соседями в базе.

        Returns:
            int: alias_numeric найденного алиаса.

        """
        alias_numeric_service = get_alias_numeric_service()

        # Дефолтное значение.
        alias_numeric = 1

        # lock alias_numeric предыдущего
        await self._lock_by_alias_numeric(alias_numeric - 1)
        # lock alias_numeric текущего
        await self._lock_by_alias_numeric(alias_numeric)
        # lock alias_numeric следующего
        await self._lock_by_alias_numeric(alias_numeric + 1)

        # Проверка существования абсолютно первого алиаса.
        absolute_first_url: ShortedUrl | None = await self.get_shorted_url_by_alias(
            alias_numeric_service.alias_symbols[0]
        )

        if absolute_first_url is None:
            return alias_numeric

        # Получение первого ShortedUrl со свободным соседом.
        previous_shorted_url: ShortedUrl | None = await (
            self.get_first_shorted_url_with_available_after()
        )

        # Проверка на несменяемость до и после lock'a.
        while previous_shorted_url is not None:
            # lock alias_numeric ссылки с доступностью создания послее нее ссылки
            alias_numeric = alias_numeric_service.get_alias_numeric_from_alias(
                previous_shorted_url.alias
            ) + 1

            # lock alias_numeric предыдущего
            await self._lock_by_alias_numeric(alias_numeric - 1)
            # lock alias_numeric текущего
            await self._lock_by_alias_numeric(alias_numeric)
            # lock alias_numeric следующего
            await self._lock_by_alias_numeric(alias_numeric + 1)

            checking_previous_shorted_url: ShortedUrl | None = await (
                self.get_first_shorted_url_with_available_after()
            )
            # Гарантирует безопасность и четкость
            if previous_shorted_url == checking_previous_shorted_url:
                break

            previous_shorted_url = checking_previous_shorted_url

        return alias_numeric

    async def _get_url_alias_numeric_with_custom_alias_with_lock(
        self,
        custom_alias: str
    ) -> int:
        """Блокирование соседей custom_alias_numeric в базе.

        Args:
            custom_alias (str): Кастомный алиас

        Raises:
            ValueError: Если custom_alias не соответствует pattern'у.

        Returns:
            int: alias_numeric

        """
        if not re.match(self.alias_pattern, custom_alias):
            msg = ("custom_alias must match pattern. Len should be from 4 to 20."
                    "Available symbols are: English symbols, digits and '-', '_' .")
            raise ValueError(msg)

        alias_numeric_service = get_alias_numeric_service()
        alias_numeric = alias_numeric_service.get_alias_numeric_from_alias(custom_alias)

        # lock alias_numeric предыдущего
        await self._lock_by_alias_numeric(alias_numeric - 1)
        # lock alias_numeric текущего
        await self._lock_by_alias_numeric(alias_numeric)
        # lock alias_numeric следующего
        await self._lock_by_alias_numeric(alias_numeric + 1)

        return alias_numeric

    async def create_new_url_with_lock(
        self,
        original_url: str,
        custom_alias: str | None = None,
        created_by_ip: str | None = None
    ) -> ShortedUrl:
        """Создание ссылки в базе с блокирование его и его соседей до коммита.

        Args:
            original_url (str): Оригинальный url.
            custom_alias (str | None, optional): Кастомный алиас. Defaults to None.
            created_by_ip (str | None, optional): IP пользователя. Defaults to None.

        Raises:
            ValueError: Если оригинальный url не соотвествует своему паттерну.
            ValueError: Если алиас уже занят.
            UnexpectedException: При ошибке непредусмотренной сервером.

        Returns:
            ShortedUrl: Обьект ShortedUrl.

        """
        if not re.match(self.original_url_pattern, original_url):
            msg = ("url must match pattern. Len should be ≤ 2048"
                    "and starts with http:// or https://")
            raise ValueError(msg)

        alias_numeric: int | None = None

        alias_numeric_service = get_alias_numeric_service()

        if custom_alias is None:
            # Если не указан custom_alias пытаемся взять незанятый алиас рандомно.
            # Данный метод эффективен на этапе, когда очень много незанятых алиасов.
            # И вместо того, чтобы брать по очереди 1 за другим, он берет рандомно.
            for attempt in range(MAX_GET_RANDOM_ALIAS_ATTEMPT_COUNT):
                start_alias: str = "".join(
                    alias_numeric_service.alias_symbols[0] for _ in range(4)
                ) # Минимум 4 символа

                min_alias_numeric: int = (
                    alias_numeric_service.get_alias_numeric_from_alias(start_alias)
                )

                # Такая формула для max_alias_numeric
                # сделает большинство первых ссылок более короткими
                end_alias: str = "".join(
                    choice(alias_numeric_service.alias_symbols) for _ in range(
                        len(start_alias),
                        (
                            len(start_alias) + 20 //
                            (MAX_GET_RANDOM_ALIAS_ATTEMPT_COUNT - attempt)
                        )
                    )
                )
                max_alias_numeric: int = (
                    alias_numeric_service.get_alias_numeric_from_alias(end_alias)
                )

                random_alias_numeric = randint(min_alias_numeric, max_alias_numeric)
                random_alias = (
                    alias_numeric_service.get_alias_from_alias_numeric(random_alias_numeric)
                )

                await self._get_url_alias_numeric_with_custom_alias_with_lock(
                    random_alias
                )

                if (await self.get_shorted_url_by_alias(random_alias)) is None:
                    alias_numeric = random_alias_numeric
                    break

            # Если все-таки рандом не удался и в базе очень много занятых алиасов =>
            # тогда берем один за другим.
            # Стоит не брать один за другим при малом количестве занятых, так как
            # они выполняются с блокировкой и очередь останавливается
            if alias_numeric is None:
                alias_numeric = await self._get_next_alias_numeric_with_lock()
        else:
            alias_numeric = await (
                self._get_url_alias_numeric_with_custom_alias_with_lock(custom_alias)
            )

        alias = alias_numeric_service.get_alias_from_alias_numeric(alias_numeric)
        available_after = False

        current_url: ShortedUrl | None = await self.get_shorted_url_by_alias(alias)
        if current_url is not None and custom_alias is not None:
            msg = "alias already taken"
            raise ValueError(msg)
        if current_url is not None and custom_alias is None:
            msg = "Unexpected error occured, please, repeat request"
            raise UnexpectedException(msg)

        previous_url: ShortedUrl | None = await self.get_shorted_url_by_alias(
            alias_numeric_service.get_alias_from_alias_numeric(alias_numeric - 1)
        )
        if previous_url is not None:
            previous_url.available_after = False

        next_url: ShortedUrl | None = await self.get_shorted_url_by_alias(
            alias_numeric_service.get_alias_from_alias_numeric(alias_numeric + 1)
        )
        if next_url is None:
            available_after = True

        shorted_url = ShortedUrl(
            created_by_ip=created_by_ip,
            original_url=original_url,
            alias=alias,
            alias_len=len(alias),
            available_after=available_after
        )
        self.db.add(shorted_url)

        await self.db.commit()
        await self.db.refresh(shorted_url)

        return shorted_url

    async def delete_url_by_alias_numeric_with_lock(self, alias_numeric: int) -> None:
        """Безопасное удаление ссылки с lock'ом по alias_numeric.

        Args:
            alias_numeric (int): Цифровой вид алиаса.

        """
        # lock alias_numeric предыдущего
        await self._lock_by_alias_numeric(alias_numeric - 1)
        # lock alias_numeric текущего
        await self._lock_by_alias_numeric(alias_numeric)

        alias_numeric_service = get_alias_numeric_service()

        alias = alias_numeric_service.get_alias_from_alias_numeric(alias_numeric)
        prev_alias = alias_numeric_service.get_alias_from_alias_numeric(
            alias_numeric - 1
        )

        # Удаление выбранной ссылки.
        delete_url_by_alias_numeric_stmt = delete(ShortedUrl).where(
            ShortedUrl.alias==alias
        )
        # Изменение предыдущей ссылки (available_after=True).
        update_url_by_alias_numeric_stmt = update(ShortedUrl).where(
            ShortedUrl.alias==prev_alias
        ).values(available_after=True)

        await self.db.execute(delete_url_by_alias_numeric_stmt)
        await self.db.execute(update_url_by_alias_numeric_stmt)
        await self.db.commit()

    async def delete_url_by_alias_with_lock(self, alias: str) -> None:
        """Безопасное удаление ссылки с lock'ом по alias.

        Конвертирование в alias_numeric и удаление по нему.

        Args:
            alias (str): Алиас ссылки.

        """
        alias_numeric = get_alias_numeric_service().get_alias_numeric_from_alias(alias)

        await self.delete_url_by_alias_numeric_with_lock(alias_numeric)

    async def add_click_to_shorted_url(self, shorted_url: ShortedUrl) -> None:
        """Добавление клика к общему количеству кликов ShortedUrl.

        Args:
            shorted_url (ShortedUrl): Сокращенная ссылка.

        """
        # В случае использования Postgresql атомарность запросов не нужна,
        # так как он сам будет блокировать.
        shorted_url.clicks += 1

        await self.db.commit()
        await self.db.refresh(shorted_url)

@lru_cache
def get_alias_numeric_service() -> AliasNumericService:
    """Получение сервиса для работы с кастомной системой счисления alias'ов.

    Returns:
        AliasNumericService: сервис для работы с кастомной системой счисления alias'ов.

    """
    return AliasNumericService()

# нет смысла в кеше, если значение db всегда разное
def get_urls_service(db: AsyncSession) -> UrlsService:
    """Получение сервис для работы с CRUD ссылок.

    Args:
        db (AsyncSession): Сессия базы данных.

    Returns:
        UrlsService: Сервис для работы с CRUD ссылок.

    """
    return UrlsService(db)
