Техническое задание
Цель: API для создания и управления короткими ссылками.

## Спецификация API

1. Создать короткую ссылку

   Метод:`POST /api/shorten`
   Тело запроса:
{
       "url": "https://длинный.пример/путь",
       "custom_alias": "alias"  // опционально
     }
Ответ 200:
{
       "alias": "abc123",
       "short_url": "https://short.domain/abc123"
     }
Ошибки:

     * 400 — неверный URL или alias уже занят
     * 429 — превышен лимит запросов

2. Редирект по alias

   Метод: GET /{alias}
   Поведение: 302 Redirect → оригинальный URL
   Ошибки: 404 — alias не найден

3. Информация о ссылке

   Метод: GET /api/links/{alias}
   Ответ 200:
{
       "original_url": "...",
       "created_at": "YYYY-MM-DDTHH:MM:SSZ",
       "clicks": 123
     }
Ошибки: 404 — alias не найден

4. Список ссылок

   Метод: GET /api/links?page=1&per_page=20
   Ответ 200: массив объектов { alias, original_url, created_at, clicks }

5. Удалить ссылку

   Метод: DELETE /api/links/{alias}
   Ответ 204 при успешном удалении
   Ошибки: 404 — alias не найден

---

Валидация:

URL — схема http/https, длина ≤ 2048
 custom_alias — латиница, цифры, дефис/подчёркивание, длина 4–20