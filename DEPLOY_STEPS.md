# Алгоритм деплоя — по шагам

От: юзер ввёл данные (репо, домен, спец-переменные).
До: рабочий проект на https://домен.

---

## Вход (что есть на старте)
- repo URL + GitHub-токен юзера
- домен
- спец-переменные (key/value), если есть
- IP сервера + SSH-доступ

---

## ШАГ 1 — Подготовка сервера (под root)
```bash
ssh root@<IP>
apt update && apt upgrade -y

# deploy-юзер
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys

# docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy

# fail2ban
apt install -y fail2ban
systemctl enable --now fail2ban
```
fail2ban jail `/etc/fail2ban/jail.local`:
```ini
[sshd]
enabled = true
maxretry = 5
bantime = 1h
```
```bash
systemctl restart fail2ban
passwd deploy
```bash
systemctl restart ssh
```
> Проверить вход `ssh deploy@<IP>` ВО ВТОРОМ терминале до выхода из root.

---

## ШАГ 2 — Клон репозитория (под deploy)
```bash
ssh deploy@<IP>
cd ~
git clone https://<TOKEN>@github.com/<user>/<repo>.git app
cd app
```

---

## ШАГ 3 — Генерация .env
Собрать .env из трёх источников и положить в корень `app`:
```
# генерим сами
SECRET_KEY=<openssl rand -hex 32>
POSTGRES_PASSWORD=<random>
DEBUG=False

# из домена
DOMAIN=<домен>
ALLOWED_HOSTS=<домен>
CSRF_TRUSTED_ORIGINS=https://<домен>
CORS_ALLOWED_ORIGINS=https://<домен>

# фикс / из шаблона юзера
POSTGRES_USER=appuser
POSTGRES_DB=appdb
DATABASE_URL=postgres://appuser:<POSTGRES_PASSWORD>@db:5432/appdb
REDIS_URL=redis://redis:6379/0

# спец-переменные юзера (если есть)
<KEY>=<VALUE>
```
```bash
chmod 600 .env
```

---

## ШАГ 4 — Положить наш слой (Caddy)
Скопировать в корень `app`:
- `docker-compose.caddy.yml`
- `Caddyfile` (берёт ${DOMAIN} из .env)

---

## ШАГ 5 — Запуск
```bash
docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d --build
```
(migrate + collectstatic отрабатывают в command приложения)

---

## ШАГ 6 — Health-check
```bash
docker compose ps                              # все up/healthy
curl -I https://<домен>/healthz/               # ждать 200 (опрос с таймаутом)
curl -I https://<домен>/static/admin/css/base.css   # 200 = статика ок
```

---

## ШАГ 7 — Финал
- deploy-and-forget: удалить спец-переменные юзера из своей БД.
- Готово: проект на https://<домен>.

---

## Предусловие (до шага 1)
DNS: A-запись <домен> -> <IP сервера>. Иначе Caddy не выпустит SSL.
