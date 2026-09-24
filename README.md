# Quanterra Collector — Zabbix 7

Collector para integrar digitalizadores **Quanterra Q330** con **Zabbix 7**.

El servicio consulta periódicamente:

    http://<Q330>:6381/stats.html

extrae las métricas operativas del Q330, descubre los equipos monitorizados mediante la API de Zabbix 7 y envía los valores al servidor Zabbix mediante Zabbix Sender.

La aplicación se ejecuta en **Docker con Python 3.12**.

## Arquitectura

    Zabbix 7 API
         │
         │ descubrimiento de hosts
         ▼
    ┌───────────────────────────────┐
    │ Quanterra Collector - Docker │
    │                               │
    │ main.py                       │
    │   │                           │
    │   ├── collector/              │
    │   │    ├── config.py          │
    │   │    ├── q330.py            │
    │   │    └── runtime.py         │
    │   │                           │
    │   ├── api/                    │
    │   └── zabbix/                 │
    └──────────────┬────────────────┘
                   │
                   │ HTTP :6381
                   ▼
             Quanterra Q330

El envío de métricas se realiza hacia Zabbix Server o Proxy mediante TCP/10051.

## Estructura del proyecto

    quanterraProject/
    ├── api/
    │   └── api_zbx_processing.py
    ├── collector/
    │   ├── config.py
    │   ├── q330.py
    │   └── runtime.py
    ├── zabbix/
    │   └── zabbix_sender.py
    ├── templates/
    │   └── quanterra_zabbix7.yaml
    ├── tests/
    │   ├── fixtures/
    │   │   └── stats.html
    │   └── test_collector.py
    ├── main.py
    ├── requirements.txt
    ├── Dockerfile
    ├── compose.yaml
    ├── .env.example
    ├── .gitignore
    ├── .dockerignore
    └── README.md

## Métricas Q330

Se conservan las diez claves históricas:

| Clave | Descripción |
| --- | --- |
| `station.code` | Código de estación |
| `serial.number` | Serial/tag del equipo |
| `q330.serial` | Número de serie Q330 |
| `input.voltage` | Voltaje de entrada [V] |
| `system.temp` | Temperatura del sistema [°C] |
| `main.current` | Corriente principal [mA] |
| `sat.used` | Satélites utilizados |
| `clock.quality` | Calidad de reloj [%] |
| `media.site1.free.space` | Espacio libre Site 1 [%] |
| `media.site2.free.space` | Espacio libre Site 2 [%] |

Adicionalmente:

| Clave | Descripción |
| --- | --- |
| `q330.collect.success` | Estado de recolección del Q330 |
| `q330.collect.metrics` | Número de métricas obtenidas |

Una recolección completa requiere las diez métricas Q330.

## Métricas del Collector

El host del collector recibe:

- `collector.heartbeat`
- `collector.uptime`
- `collector.cycle.duration`
- `collector.devices.total`
- `collector.devices.failed`
- `collector.cycle.success`

Estas métricas permiten supervisar el propio proceso de adquisición.

## Template Zabbix 7

Importar:

    templates/quanterra_zabbix7.yaml

desde:

**Data collection → Templates → Import**

El archivo contiene:

- `Quanterra Q330 by collector`
- `Quanterra collector health`

Vincule `Quanterra Q330 by collector` únicamente a los hosts Q330.

Cree además un host habilitado cuyo nombre técnico sea:

    Quanterra collector

y vincule `Quanterra collector health`.

El nombre puede modificarse mediante `COLLECTOR_HOST`.

## Descubrimiento de Q330

El collector utiliza un API Token de Zabbix y busca los hosts habilitados asociados al template configurado en:

    ZABBIX_TEMPLATE

Para cada host utiliza su interfaz principal y obtiene la IP o DNS del Q330.

El puerto configurado en la interfaz de Zabbix no se utiliza para consultar el equipo. El acceso HTTP utiliza:

    Q330_PORT=6381

## Configuración

Copiar:

    cp .env.example .env

Variables principales:

| Variable | Uso |
| --- | --- |
| `ZABBIX_URL` | URL de la API Zabbix |
| `ZABBIX_SERVER` | Zabbix Server o Proxy receptor |
| `ZABBIX_PORT` | Puerto sender, por defecto `10051` |
| `ZABBIX_TEMPLATE` | Template utilizado para descubrir Q330 |
| `COLLECTOR_HOST` | Nombre técnico del host collector |
| `COLLECTOR_INTERVAL` | Intervalo entre ciclos |
| `COLLECTOR_TIMEOUT` | Timeout de comunicaciones |
| `COLLECTOR_WORKERS` | Consultas Q330 concurrentes |
| `COLLECTOR_HEALTH_MAX_AGE` | Edad máxima del último ciclo válido |
| `Q330_PORT` | Puerto HTTP del Q330, por defecto `6381` |

## API Token

El token no debe almacenarse en Git ni dentro de `.env`.

Crear:

    mkdir -p secrets

Guardar exclusivamente el token en:

    secrets/zabbix_token

sin comillas ni variables adicionales.

Compose lo monta dentro del contenedor como:

    /run/secrets/zabbix_token

El usuario asociado al token requiere acceso de lectura a los hosts y templates utilizados por el collector.

## Seguridad

El contenedor:

- se ejecuta con UID `10001`;
- utiliza filesystem raíz de solo lectura;
- elimina capabilities Linux;
- activa `no-new-privileges`;
- no publica puertos;
- mantiene el token fuera de la imagen;
- utiliza `/tmp` mediante `tmpfs`.

Los archivos `.env`, `secrets/` y logs están excluidos de Git.

## Allowed hosts

Los items trapper utilizan:

    {$COLLECTOR.ALLOWED_HOSTS}

El valor inicial del template es:

    127.0.0.1

Antes del despliegue debe cambiarse por la IP o red de origen que realmente observa Zabbix Server/Proxy para las conexiones procedentes del collector.

No abra este parámetro indiscriminadamente a todas las redes.

## Construcción

    docker build -t quanterra-collector:test .

Para reconstrucción completa:

    docker build --no-cache -t quanterra-collector:test .

## Pruebas

Ejecutar:

    docker run --rm \
      -v "$PWD:/workspace:ro" \
      -w /workspace \
      --entrypoint python \
      quanterra-collector:test \
      -m unittest discover -s tests -v

Actualmente las pruebas cubren:

- parser Q330;
- variantes del HTML;
- respuestas incompletas;
- validación de métricas;
- IP y DNS;
- API Token;
- timeout HTTP;
- errores HTTP;
- Zabbix Sender;
- healthcheck;
- correspondencia entre métricas y template Zabbix.

`tests/fixtures/stats.html` es una fixture sintética utilizada para pruebas de regresión.

Además del conjunto automatizado, el parser fue validado contra un Q330 real accesible por HTTP/6381.

## Docker Compose

Validar primero:

    docker compose config --quiet

Arrancar:

    docker compose up -d --build

Ver estado:

    docker compose ps

Logs:

    docker compose logs -f collector

Healthcheck:

    docker compose exec collector python main.py --healthcheck

Detener:

    docker compose down

## Logs

El collector escribe en stdout/stderr y en:

    /app/logs/collector.log

El archivo utiliza rotación automática.

Compose mantiene `/app/logs` mediante el volumen:

    collector_logs

## Healthcheck

Docker ejecuta:

    python main.py --healthcheck

El estado es válido cuando el pipeline terminó recientemente y los envíos hacia Zabbix fueron aceptados.

La indisponibilidad individual de un Q330 no implica que el proceso collector esté detenido. Estas fallas se reflejan mediante:

    q330.collect.success
    collector.devices.failed

Una falla de API o Zabbix Sender invalida el healthcheck.

## Alertas iniciales

El template incorpora macros iniciales:

    {$Q330.VOLTAGE.MIN}=11
    {$Q330.TEMP.MAX}=60
    {$Q330.CLOCK.MIN}=90
    {$Q330.SAT.MIN}=4
    {$Q330.MEDIA.MIN}=10
    {$COLLECTOR.NODATA}=5m

Estos valores son valores iniciales de operación y deben ajustarse de acuerdo con los criterios técnicos definidos para la red.

## Despliegue inicial recomendado

Realizar la integración de forma progresiva:

1. Importar el template Zabbix 7.
2. Crear el host `Quanterra collector`.
3. Configurar el API Token.
4. Configurar `.env`.
5. Determinar la IP de origen observada por Zabbix Sender.
6. Configurar `{$COLLECTOR.ALLOWED_HOSTS}`.
7. Vincular inicialmente un solo Q330.
8. Ejecutar un ciclo de prueba.
9. Verificar **Monitoring → Latest data**.
10. Verificar triggers y healthcheck.
11. Ampliar posteriormente al resto de Q330.

No ejecutar simultáneamente el collector antiguo y el nuevo sobre los mismos hosts durante la migración.

## Dependencias

`requirements.txt` contiene únicamente:

    requests==2.32.5
    zabbix_utils==2.0.4
    PyYAML==6.0.2

`PyYAML` se utiliza para validar el template durante las pruebas automatizadas.

## Estado de la migración

Validado hasta el momento:

- Docker con Python 3.12.
- Parser Q330.
- Acceso HTTP/6381 a Q330 real.
- Diez métricas Q330 obtenidas correctamente.
- Zabbix API implementada mediante API Token.
- Zabbix Sender implementado mediante `zabbix_utils`.
- Template nativo Zabbix 7.
- Healthcheck del collector.
- 19 pruebas automatizadas exitosas.

Pendiente de validación de extremo a extremo:

    Q330 → Docker Collector → Zabbix 7 → Latest data → Triggers
