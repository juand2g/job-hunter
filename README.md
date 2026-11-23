# Job Hunter

Motor de automatización para la búsqueda de empleo remoto: agrega vacantes de
múltiples fuentes, las normaliza, las puntúa por relevancia y te notifica por
Telegram las mejores oportunidades — 24/7, con dashboard propio y match con LLM.

**Stack:** Python · FastAPI · MongoDB · Docker · Nuxt · Telegram · LLM (DeepSeek)

## Estado actual (Fase 0 + 1)

- [x] Repo + `docker-compose` (Mongo + API FastAPI)
- [x] Fuente real conectada: RemoteOK y Remotive
- [x] Normalización de vacantes a un esquema único
- [x] Clasificación de ubicación (filtro LATAM/Colombia)
- [x] Fase 2: dedup (upsert) + scoring/filtro por keywords
- [x] Filtro de senioridad (junior/mid/senior)
- [x] Fase 3: notificación Telegram en match alto
- [x] Fase 4: dashboard Nuxt/Vue
- [x] Fase 5: match con LLM + CV personalizado
- [x] Fase 6: correr 24/7 con systemd timer (local)
- [x] Fase 7a: tracking de postulaciones + detección `apply_type`
- [ ] Fase 7b: auto-fill asistido (Greenhouse/Lever) + borrador de screener

## Requisitos

- Docker + Docker Compose
- Node.js 20+ (para el frontend)

## Cómo correrlo

```bash
cp .env.example .env
make up          # levanta Mongo + API
make fetch       # descarga vacantes y las guarda en Mongo
make stats       # ve cuántas hay y de qué fuente
```

### Frontend (dashboard Nuxt)

```bash
cd frontend
npm install
npm run dev      # http://localhost:3001
```

El dashboard consume el API en `http://localhost:8000`. Si el API vive en otra
URL, defínela con `NUXT_PUBLIC_API_BASE`. El puerto 3001 está fijado en
`nuxt.config.ts` porque el 3000 suele estar ocupado.

Endpoints:

- `GET /jobs?latam=true&matched=true&seniority=mid&max_age=30` — lista vacantes (filtros opcionales)
- `GET /matches?seniority=junior|mid|senior&max_age=30` — solo vacantes que hacen match con tu perfil (score desc)
- `GET /stats` — totales por fuente y por senioridad
- `POST /fetch` — dispara una descarga manual
- `POST /notify_test` — envía un mensaje de prueba a Telegram
- `POST /match/{job_id}` — evalúa una vacante con LLM (score, requisitos, gaps)
- `POST /cv/{job_id}` — genera un CV personalizado para esa vacante
- `PATCH /jobs/{job_id}/application` — actualiza el estado de postulación (`status`, `notes`)
- `GET /application-statuses` — lista de estados válidos

El scoring (Fase 2) asigna a cada vacante `score`, `matched` y
`matched_keywords`/`excluded_keywords` usando las listas de
`app/matching/keywords.py`. Los matches reales están en `GET /matches`.

La senioridad (`app/matching/seniority.py`) clasifica cada vacante en
`junior`, `mid`, `senior` o `unknown` según el título (senior/lead/staff/
arquitecto vs junior/jr/trainee vs mid-level/intermediate) y, si el título no
da pista, por años de experiencia en la descripción. Úsala para apuntar a roles
de tu nivel: `GET /matches?seniority=mid`.

Cada vacante expone `age_days` (días desde que se publicó, o desde que se vio
por primera vez si la fuente no trae fecha). Filtra por frescura con
`max_age` (en días): `GET /matches?max_age=30`.

## Fuentes de datos

| Fuente    | Tipo | Auth | Notas |
|-----------|------|------|-------|
| RemoteOK  | API JSON | No | Fuente principal (~98 jobs). Incluir link de vuelta. |
| Remotive  | API JSON | No | Tier gratis limitado (~13 jobs). Máx 4 llamadas/día. Requiere atribución. |
| Greenhouse / Lever | JSON público por empresa | No | Añadir en Fase 7. Sin límites, ideal para postular. |

Aviso legal de Remotive: la API es pública para compartir sus vacantes; exige
enlazar de vuelta a la URL original de Remotive y mencionar a Remotive como
fuente. No hay que pedir sus datos con demasiada frecuencia (máx. ~4 veces/día).

## Notificación por Telegram (Fase 3)

Para recibir alertas de vacantes nuevas con alto match:

1. Crea un bot con [@BotFather](https://t.me/BotFather) y copia el token.
2. Obtén tu `chat_id` (p. ej. con [@userinfobot](https://t.me/userinfobot)).
3. Añade a `.env`:
   ```
   TELEGRAM_TOKEN=tu-token
   TELEGRAM_CHAT_ID=tu-chat-id
   MATCH_SCORE_THRESHOLD=5
   ```
4. Abre `t.me/<tu_bot>` y pulsa **/start** (obligatorio la primera vez).
5. Verifica con `curl -X POST http://localhost:8000/notify_test`.

Cuando `make fetch` detecta una vacante **nueva** que hace match con score
`>= MATCH_SCORE_THRESHOLD` y es apta para LATAM, te llega un mensaje con
título, empresa, senioridad, score, salario y enlace.

## Match con LLM y CV personalizado (Fase 5)

Usa un LLM compatible con la API de OpenAI (DeepSeek por defecto) para dos cosas:

- `POST /match/{job_id}`: puntúa la vacante contra tu perfil y devuelve `score`,
  `reasoning`, `key_requirements`, `matched_skills` y `gaps`.
- `POST /cv/{job_id}`: reescribe tu CV resaltando lo relevante para esa vacante.

Configuración en `.env`:

```
LLM_API_KEY=tu-key
LLM_BASE_URL=https://api.deepseek.com   # o tu endpoint compatible
LLM_MODEL=deepseek-chat
```

Tu perfil base vive en `backend/app/profile.py` (texto fijo, edítalo ahí).

## Filtro de ubicación (Colombia)

Cada vacante se clasifica con `classify_location()` en
`app/pipeline/normalize.py`. El campo `latam_friendly` es `True` si la ubicación
menciona Colombia, LATAM, Latinoamérica, Suramérica, Americas, Worldwide,
Anywhere o Global. `remote` indica si es remoto en general.

En RemoteOK la ubicación vacía significa "Anywhere" (remoto mundial), así que
esas vacantes se marcan como `latam_friendly`. En Remotive se usa
"Worldwide"/"USA" explícitamente, por lo que no aplica la misma regla.

Para filtrar solo vacantes aptas desde Colombia:

```bash
curl "http://localhost:8000/jobs?latam=true"
```

## Correr 24/7 en esta PC (Fase 6)

El stack arranca solo con el sistema (Docker `enabled` + `restart: unless-stopped`
en los contenedores). El fetch automático se hace con un systemd timer:

```bash
sudo cp deploy/jobhunter-fetch.service deploy/jobhunter-fetch.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jobhunter-fetch.timer
systemctl list-timers jobhunter-fetch
```

- `jobhunter-fetch.timer`: cada 6 h (`Persistent=true` + delay aleatorio).
- `jobhunter-fetch.service`: oneshot que ejecuta `scripts/fetch.sh` (fetch + alerta Telegram).
- Logs: `journalctl -u jobhunter-fetch.service`.

## Estructura

```
backend/app/
├── main.py          # API FastAPI
├── config.py        # configuración (env vars)
├── db.py            # conexión MongoDB (motor)
├── models.py        # esquema de vacante (Pydantic)
├── runner.py        # descarga + scoring + upsert en Mongo
├── sources/         # un adaptador por fuente
│   ├── remoteok.py
│   └── remotive.py
├── matching/        # scoring por keywords y senioridad
│   ├── keywords.py
│   ├── scorer.py
│   └── seniority.py
└── pipeline/
    └── normalize.py # clasificación de ubicación y fechas

frontend/
├── nuxt.config.ts   # Nuxt 4, puerto 3001, apiBase
├── app/
│   ├── app.vue
│   ├── pages/index.vue      # dashboard
│   ├── composables/useApi.ts # cliente del API
│   └── assets/main.css
```
