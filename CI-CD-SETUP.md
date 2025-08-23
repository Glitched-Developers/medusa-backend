М# Упрощённая настройка CI/CD

## 🚀 Что делает pipeline:
- ✅ Запускает тесты
- ✅ Проверяет качество кода
- ✅ Собирает Docker образ
- ✅ Загружает на GitHub Container Registry (ghcr.io)

## ⚙️ Настройка

### 1. В GitLab Settings → CI/CD → Variables добавьте:

```
GITHUB_USERNAME = ваш-github-username
GITHUB_TOKEN = ваш-github-personal-access-token
```

### 2. Создание GitHub Token:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Выберите scopes: `write:packages`, `read:packages`
4. Скопируйте токен в переменную `GITHUB_TOKEN`

## 🏃‍♂️ Запуск

### Локальная разработка:
```bash
cp .env.example .env
docker-compose up --build
```

### Продакшен (используя готовый образ):
```bash
# Отредактируйте docker-compose.yml:
# Закомментируйте build: .
# Раскомментируйте image: ghcr.io/your-username/medusa-backend:latest

docker-compose up
```

Это всё! ✨