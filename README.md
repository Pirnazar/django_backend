# Cargo Warehouse Backend (Django)

Это серверная часть (backend) системы управления складом и логистикой, написанная на Django.

## Технологический стек
- **Язык**: Python 3.12
- **Фреймворк**: Django / Django REST Framework
- **База данных**: PostgreSQL 15
- **Кэш/Очереди**: Redis 7
- **Фоновые задачи**: Celery
- **Тестирование**: Pytest + Factory Boy
- **Инфраструктура**: Docker, Docker Compose

---

## 🚀 Быстрый запуск через Docker (Рекомендуется)

Самый простой способ запустить проект — использовать Docker Compose, который автоматически поднимет базу данных PostgreSQL, Redis, Celery и само Django приложение.

### Требования
- Установленный [Docker](https://docs.docker.com/get-docker/) и Docker Compose.

### Инструкция по запуску

1. **Клонируйте репозиторий и перейдите в папку проекта**:
   ```bash
   cd d:/Projects/Cargo/Warehouse/backend_django
   ```

2. **Настройте переменные окружения**:
   Скопируйте пример конфигурации и при необходимости отредактируйте:
   ```bash
   cp .env.example .env
   ```

3. **Соберите и запустите контейнеры**:
   ```bash
   docker-compose up --build -d
   ```
   *Флаг `-d` запускает контейнеры в фоновом режиме.*

4. **Примените миграции базы данных**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Создайте суперпользователя (администратора)**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

   docker-compose exec web python manage.py compilemessages

6. **Проект доступен по адресу**:
   - API / Сайт: [http://localhost:8000](http://localhost:8000)
   - Админ-панель: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 💻 Локальный запуск (без Docker для Web)

Если вы хотите разрабатывать проект локально (например, используя виртуальное окружение `venv`), следуйте этой инструкции.

### Требования
- Python 3.12+
- Запущенные PostgreSQL и Redis (можно поднять их через Docker).

### Инструкция по настройке

1. **Запустите БД и Redis (через Docker)**:
   Вы можете поднять только нужные сервисы из `docker-compose.yml`:
   ```bash
   docker-compose up -d db redis
   ```

2. **Создайте и активируйте виртуальное окружение**:
   ```bash
   python -m venv venv
   
   # Для Windows:
   venv\Scripts\activate
   
   # Для Linux/Mac:
   source venv/bin/activate
   ```

3. **Установите зависимости**:
   ```bash
   pip install -r requirements/local.txt
   ```

4. **Настройте `.env` файл**:
   Убедитесь, что параметры подключения к БД и Redis указывают на `localhost` (если вы подняли их локально), а не на имена контейнеров.
   ```env
   DATABASE_URL=postgres://cargo_user:cargo_password@localhost:5432/cargo_db
   REDIS_URL=redis://localhost:6379/0
   ```

5. **Примените миграции**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Создайте суперпользователя**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Запустите сервер разработки**:
   ```bash
   python manage.py runserver
   ```

---

## 🧪 Тестирование

Проект использует `pytest` для тестирования. 

Для запуска тестов локально (при активированном `venv`):
```bash
pytest
```
Или стандартной командой Django:
```bash
python manage.py test
```

Для запуска тестов внутри Docker:
```bash
docker-compose exec web pytest
```

---

## 🛠 Полезные команды Docker Compose

- Остановка всех сервисов:
  ```bash
  docker-compose down
  ```
- Просмотр логов веб-сервиса:
  ```bash
  docker-compose logs -f web
  ```
- Перезапуск Celery воркера:
  ```bash
  docker-compose restart celery_worker
  ```
