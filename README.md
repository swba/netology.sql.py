# Домашнее задание по теме «Работа с PostgreSQL из Python»

Данный проект реализует простейший менеджер клиентов с сохранением данных в БД
PostgreSQL.

Программная логика реализована в модуле `client_manager`, который содержит
следующие файлы:

- `client_manager.py` &mdash; реализация класса `ClientManager`, который и
предоставляет весь функционал по работе с клиентами.
- `errors.py` &mdash; определения классов ошибок, возникающих при работе с
менеджером клиентов.
- `model.py` &mdash; определения модельных классов (в данном случае содержит
лишь один класс `Client`).
- `types.py` &mdash; определения вспомогательных типов данных, которые 
используются для типизации параметров и результатов методов.

Помимо основного модуля, проект содержит следующие файлы:

- `client_manager_test.py` &mdash; определяет функцию `test_client_manager`,
которая является одновременно и тестом менеджера клиентов, и образцом работы
с его методами.
- `db.txt` &mdash; строка подключения к базе данных PostgreSQL. Для тестирования 
проекта поменяйте реквизиты доступа к БД на собственные.

## Менеджер клиентов `ClientManager`

Менеджер клиентов `ClientManager` предоставляет следующие публичные методы:

- `setup()` &mdash; удаляет, а затем заново создаёт в БД таблицы для хранения
данных клиентов.
- `ensure_tables()` &mdash; создаёт в БД таблицы для хранения данных клиентов,
если они ещё не существуют.
- `drop_tables()` &mdash; удаляет из БД таблицы для хранения данных клиентов.
- `add_client(values: ContactValues) -> Client` &mdash; сохраняет в БД нового
клиента и возвращает соответствующий объект.
- `load_client(client_id: int) -> Client | None` &mdash; загружает данные клиента
из БД и возвращает соответствующий объект.
- `load_clients(client_ids: list[int]) -> dict[int, Client] | None` &mdash;
загружает из БД данные нескольких клиентов по их ID и возвращает словарь 
соответствующих объектов (с идентификаторами клиентов в качестве ключей).
- `update_client(client: Client) -> Client | None` &mdash; обновляет данные 
клиента в БД и возвращает соответствующий обновлённый объект.
- `delete_client(client_id: int)` &mdash; удаляет данные клиента из БД по его
идентификатору.
- `search_clients(values: ClientSearchValues) -> dict[int, Client] | None` 
&mdash; ищет клиентов в БД по их частичным данным и возвращает словарь 
соответствующих объектов (с идентификаторами клиентов в качестве ключей).
- `add_phone_number(client_id: int, phone_number: str) -> Client` &mdash; 
добавляет в БД телефонный номер клиента и возвращает соответствующий обновлённый
объект.
- `delete_phone_number(client_id: int, phone_number: str) -> Client` &mdash; 
удаляет телефонный номер клиента из БД.