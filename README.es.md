<p align="right"><a href="README.md">English</a></p>

# <p align="center">Quanterra Q330 Collector</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-29.1-2496ED?logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://www.zabbix.com/"><img src="https://img.shields.io/badge/Zabbix-7.0.x-D40000" alt="Zabbix"></a>
  <a href="https://github.com/rotoapanta/quanterraProject/issues"><img src="https://img.shields.io/github/issues/rotoapanta/quanterraProject" alt="GitHub issues"></a>
  <a href="https://github.com/rotoapanta/quanterraProject"><img src="https://img.shields.io/github/repo-size/rotoapanta/quanterraProject" alt="GitHub repo size"></a>
  <a href="https://github.com/rotoapanta/quanterraProject/commits/master"><img src="https://img.shields.io/github/last-commit/rotoapanta/quanterraProject" alt="GitHub last commit"></a>
  <a href="https://www.linux.org/"><img src="https://img.shields.io/badge/Platform-Linux-orange" alt="Linux"></a>
  <a href="https://github.com/rotoapanta/quanterraProject/releases/tag/v2.0.0-zabbix7"><img src="https://img.shields.io/badge/Version-v2.0.0--zabbix7-brightgreen" alt="Version"></a>
  <a href="https://www.linkedin.com/in/roberto-carlos-toapanta-g/"><img src="https://img.shields.io/badge/Autor-Roberto%20Toapanta-brightgreen" alt="Autor"></a>
  <a href="https://github.com/rotoapanta/quanterraProject/fork"><img src="https://img.shields.io/github/forks/rotoapanta/quanterraProject?style=social" alt="GitHub forks"></a>
</p>

**Quanterra Q330 Collector** es un servicio de adquisición y monitoreo
basado en Docker para integrar instrumentación Quanterra Q330/PB44 con
**Zabbix 7**.

El collector descubre los equipos monitorizados mediante la API de
Zabbix, obtiene información operativa desde la interfaz HTTP del
Q330/PB44, procesa métricas del equipo y del almacenamiento y envía la
telemetría a Zabbix mediante el protocolo trapper.

------------------------------------------------------------------------


## 📊 Resumen del proyecto

| Componente | Implementación actual |
|------------|-----------------------|
| Instrumentación soportada | Quanterra Q330 / PB44 |
| Plataforma de monitoreo | Zabbix 7.0.x |
| Templates Zabbix | 2 |
| Items Zabbix | 54 en total (48 dispositivo + 6 collector) |
| Triggers Zabbix | 10 en total (8 dispositivo + 2 collector) |
| Pruebas automatizadas | 43 |
| Entorno de ejecución | Docker |
| Transporte de telemetría | Zabbix trapper |
| Adquisición del dispositivo | HTTP |
| Tag actual | `v2.0.0-zabbix7` |

El proyecto monitorea tanto la **instrumentación Q330/PB44** como el
**pipeline del collector**, proporcionando telemetría de los equipos,
monitoreo del almacenamiento, métricas derivadas, estado de la
adquisición y visibilidad operativa desde un único despliegue Zabbix.

------------------------------------------------------------------------

## ✨ Características

-   Monitoreo HTTP de Quanterra Q330/PB44.
-   Descubrimiento mediante API de Zabbix 7.
-   Envío mediante Zabbix trapper.
-   Métricas operativas y de salud del Q330.
-   Monitoreo de medios PB44.
-   Espacio libre y ocupado por medio.
-   Ocupación total ponderada según capacidad física.
-   Automonitoreo del collector.
-   Adquisición concurrente.
-   Reintentos HTTP.
-   Manejo de respuestas incompletas y variantes.
-   Healthcheck de Docker.
-   Logs con rotación.
-   API Token mediante Docker secrets.
-   Filesystem raíz del contenedor de solo lectura.
-   Pruebas automatizadas de regresión.
-   Templates nativos para Zabbix 7.

------------------------------------------------------------------------

## 🛠️ Requisitos

  Componente                Requisito
  ------------------------- -------------------
  Python                    3.12+
  Docker                    Recomendado
  Docker Compose            v2
  Zabbix                    7.x
  Interfaz HTTP Q330/PB44   TCP/6381
  Protocolo Zabbix Sender   TCP/10051
  Sistema operativo         Linux recomendado

Entorno validado:

``` text
Python 3.12.14
Docker 29.1.3
Docker Compose 2.40.3
```

------------------------------------------------------------------------

## 🏗️ Arquitectura

``` text
                    API Zabbix 7
                         │
                         │ Descubrimiento
                         ▼
              ┌──────────────────────┐
              │ Quanterra Collector  │
              │       Docker         │
              │                      │
              │ main.py              │
              │ collector/           │
              │ api/                 │
              │ zabbix/              │
              └───────┬────────┬─────┘
                      │        │
             HTTP/6381│        │TCP/10051
                      │        │
                      ▼        ▼
                Q330 / PB44   Zabbix 7
```

------------------------------------------------------------------------

## 🗂️ Estructura del proyecto

``` text
quanterraProject/
├── api/
│   ├── __init__.py
│   └── api_zbx_processing.py
├── collector/
│   ├── __init__.py
│   ├── config.py
│   ├── q330.py
│   └── runtime.py
├── templates/
│   └── quanterra_zabbix7.yaml
├── tests/
│   ├── fixtures/
│   │   └── stats.html
│   └── test_collector.py
├── zabbix/
│   ├── __init__.py
│   └── zabbix_sender.py
├── main.py
├── compose.yaml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .dockerignore
├── .gitignore
├── README.md
└── README.es.md
```

------------------------------------------------------------------------

## 🚀 Instalación

``` bash
git clone git@github.com:rotoapanta/quanterraProject.git
cd quanterraProject
cp .env.example .env
mkdir -p secrets
```

Guardar exclusivamente el API Token de Zabbix en:

``` text
secrets/zabbix_token
```

No añadir comillas ni nombres de variables al archivo del secreto.

------------------------------------------------------------------------

## ⚙️ Configuración

El template de descubrimiento actual es:

``` text
Template Zabbix Trapper Quanterra
```

El host técnico del collector es:

``` text
Monitoring Data Collector
```

Los principales parámetros se configuran mediante `.env`.

------------------------------------------------------------------------

## 📊 Templates Zabbix

| Template | Items | Triggers | Macros |
|----------|------:|---------:|-------:|
| `Template Zabbix Trapper Quanterra` | 48 | 8 | 7 |
| `Monitoring Data Collector Health` | 6 | 2 | 2 |
| **Total** | **54** | **10** | **9** |

El archivo de importación es `templates/quanterra_zabbix7.yaml`.

Se importa desde **Recolección de datos → Plantillas → Importar**.

### 📈 Principales métricas Zabbix

| Métrica | Key | Unidad |
|---------|-----|--------|
| Voltaje de entrada | `input.voltage` | `V` |
| Temperatura del sistema | `system.temp` | `°C` |
| Corriente principal | `main.current` | `mA` |
| Satélites utilizados | `sat.used` | — |
| Calidad del reloj | `clock.quality` | `%` |
| Fase del reloj | `clock.phase` | `us` |
| Corriente de antena GPS | `gps.antenna.current` | `mA` |
| Voltaje UPS PB44 | `pb44.ups.voltage` | `V` |
| Voltaje primario PB44 | `pb44.primary.voltage` | `V` |
| Temperatura PB44 | `pb44.temperature` | `°C` |
| Datos recibidos | `data.received.bps.minute` | `Bps` |
| Latencia de datos | `data.latency` | `s` |
| Latencia de estado | `status.latency` | `s` |
| Capacidad media site 1 | `media.site1.capacity` | `MB` |
| Capacidad media site 2 | `media.site2.capacity` | `MB` |
| Ocupación total de media | `media.total.space.occupied` | `%` |
| Colección Q330 completa | `q330.collect.success` | — |
| Métricas Q330 procesadas | `q330.collect.metrics` | — |
| Heartbeat del collector | `collector.heartbeat` | `unixtime` |
| Duración del ciclo | `collector.cycle.duration` | `s` |
| Dispositivos fallidos o incompletos | `collector.devices.failed` | — |
| Ciclo del collector exitoso | `collector.cycle.success` | — |

### 🚨 Triggers Zabbix

| Template | Trigger | Severidad |
|----------|---------|-----------|
| Q330 | Voltaje de entrada bajo | Warning |
| Q330 | Temperatura del sistema alta | Warning |
| Q330 | Pocos satélites | Warning |
| Q330 | Calidad del reloj baja | Warning |
| Q330 | Uso total de media 60–80% | Warning |
| Q330 | Uso total de media ≥80% | High |
| Q330 | Sin datos del collector | High |
| Q330 | Colección fallida o incompleta | Warning |
| Collector | Sin pipeline exitoso | High |
| Collector | Dispositivos fallidos o incompletos | Warning |

------------------------------------------------------------------------

## 🗺️ Etiquetas de mapas Zabbix

Los hosts Q330/PB44 pueden mostrar sus principales métricas operativas directamente en los mapas de Zabbix. La siguiente etiqueta reutilizable puede asignarse a un elemento de tipo host:

```text
{HOST.NAME}
IP: {HOST.CONN}
Input Voltage: {?last(//input.voltage)}
Media Site 1 Space Occupied: {?last(//media.site1.space.occupied)}
Media Site 2 Space Occupied: {?last(//media.site2.space.occupied)}
Total Space Occupied: {?last(//media.total.space.occupied)}
Clock Quality: {?last(//clock.quality)}
Sat. Used: {?last(//sat.used)}
System Temperature: {?last(//system.temp)}
```

La sintaxis `//` utiliza el host asociado al elemento actual del mapa, permitiendo reutilizar la misma etiqueta sin escribir nombres de host de forma fija.

------------------------------------------------------------------------

## 💾 Monitoreo de almacenamiento

El collector monitorea los medios físicos del PB44/Q330 y calcula su
utilización.

``` text
media.site1.free.space
media.site2.free.space
media.total.space.occupied
```

La ocupación total se calcula ponderando la capacidad real de los medios
válidos, evitando promedios incorrectos cuando las capacidades son
diferentes. También se soportan equipos que poseen un solo medio físico
válido.

### Triggers de almacenamiento

``` text
60% ≤ ocupado < 80%  → WARNING
ocupado ≥ 80%        → HIGH
```

------------------------------------------------------------------------

## ❤️ Salud del Collector

  Key                          Propósito
  ---------------------------- --------------------------------
  `collector.heartbeat`        Última actividad del collector
  `collector.uptime`           Tiempo de funcionamiento
  `collector.cycle.duration`   Duración del ciclo
  `collector.devices.total`    Equipos procesados
  `collector.devices.failed`   Equipos fallidos
  `collector.cycle.success`    Estado global del ciclo

Template: `Monitoring Data Collector Health`.

------------------------------------------------------------------------

## 🔐 Allowed Hosts

Los items trapper utilizan `{$COLLECTOR.ALLOWED_HOSTS}`. Este valor debe
coincidir con la IP o red de origen que realmente observa Zabbix
Server/Proxy.

El valor por defecto actual en el YAML es:

``` text
172.22.0.0/16
```

En producción debe restringirse a la dirección o red requerida.

------------------------------------------------------------------------

## 📝 Logging

El collector utiliza `logging` de Python y registra información de
ejecución en stdout/stderr y en el archivo configurado. Se soporta
rotación de logs.

``` text
logs/collector.log
/app/logs/collector.log
```

Docker Compose conserva los logs mediante el volumen `collector_logs`.

------------------------------------------------------------------------

## 🩺 Healthcheck

``` bash
docker compose exec collector python main.py --healthcheck
```

------------------------------------------------------------------------

## ▶️ Docker Compose

``` bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs -f collector
```

Para detener:

``` bash
docker compose down
```

------------------------------------------------------------------------

## 🧪 Pruebas

``` bash
docker compose run --rm \
  --no-deps \
  --entrypoint python \
  -v "$PWD:/src:ro" \
  -w /src \
  collector \
  -m unittest discover -s tests -v
```

Resultado validado:

``` text
Ran 43 tests
OK
```

------------------------------------------------------------------------

## 📦 Dependencias

``` text
requests==2.32.5
zabbix_utils==2.0.4
PyYAML==6.0.2
```

------------------------------------------------------------------------

## 🔒 Seguridad

-   Usuario no root.
-   Filesystem raíz de solo lectura.
-   Capabilities Linux eliminadas.
-   `no-new-privileges`.
-   API Token mediante Docker secret.
-   Sin puertos de aplicación publicados.
-   `/tmp` temporal.
-   `.env` y `secrets/` excluidos de Git.

Nunca almacenar el API Token ni el `.env` de producción en Git.

------------------------------------------------------------------------

## 🔍 Flujo principal

``` text
API Zabbix
    │
    ▼
Descubrir Q330
    │
    ▼
Consultar HTTP/6381
    │
    ▼
Procesar Q330/PB44
    │
    ▼
Calcular métricas derivadas
    │
    ▼
Zabbix Sender
    │
    ▼
Zabbix Server :10051
```

------------------------------------------------------------------------

## 💬 Contacto / Soporte

robertocarlos.toapanta@gmail.com

## 👥 Autor

-   [@rotoapanta](https://github.com/rotoapanta)

------------------------------------------------------------------------

## 🔗 Enlaces

[![GitHub](https://img.shields.io/badge/GitHub-rotoapanta-181717?style=for-the-badge&logo=github)](https://github.com/rotoapanta)

[![LinkedIn](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/roberto-carlos-toapanta-g/)