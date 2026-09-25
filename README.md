<p align="right"><a href="README.es.md">Español</a></p>

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
  <a href="https://www.linkedin.com/in/roberto-carlos-toapanta-g/"><img src="https://img.shields.io/badge/Author-Roberto%20Toapanta-brightgreen" alt="Author"></a>
  <a href="https://github.com/rotoapanta/quanterraProject/fork"><img src="https://img.shields.io/github/forks/rotoapanta/quanterraProject?style=social" alt="GitHub forks"></a>
</p>

**Quanterra Q330 Collector** is a Docker-based acquisition and
monitoring service for integrating Quanterra Q330/PB44 instrumentation
with **Zabbix 7**.

The collector discovers monitored devices through the Zabbix API,
retrieves operational information from the Q330/PB44 HTTP interface,
parses device and storage health metrics, and sends telemetry to Zabbix
through the trapper protocol.

------------------------------------------------------------------------


## 📊 Project Overview

| Component | Current implementation |
|-----------|------------------------|
| Supported instrumentation | Quanterra Q330 / PB44 |
| Monitoring platform | Zabbix 7.0.x |
| Zabbix templates | 2 |
| Zabbix items | 54 total (48 device + 6 collector) |
| Zabbix triggers | 10 total (8 device + 2 collector) |
| Automated tests | 43 |
| Runtime | Docker |
| Telemetry transport | Zabbix trapper |
| Device acquisition | HTTP |
| Current release tag | `v2.0.0-zabbix7` |

The project monitors both the **Q330/PB44 instrumentation layer** and
the **collector pipeline itself**, providing device telemetry, media
storage monitoring, derived metrics, collection health and operational
visibility from a single Zabbix deployment.

------------------------------------------------------------------------

## ✨ Features

-   Quanterra Q330/PB44 HTTP monitoring.
-   Zabbix 7 API-based device discovery.
-   Zabbix trapper telemetry.
-   Q330 operational and health metrics.
-   PB44 media monitoring.
-   Per-media free-space and occupied-space metrics.
-   Weighted total media storage utilization.
-   Collector self-monitoring.
-   Concurrent device collection.
-   HTTP retry handling.
-   Parser validation for incomplete and variant responses.
-   Docker healthcheck.
-   Rotating application logs.
-   API token support through Docker secrets.
-   Read-only container filesystem.
-   Automated regression tests.
-   Native Zabbix 7 templates.

------------------------------------------------------------------------

## 🛠️ System Requirements

  Component                  Requirement
  -------------------------- -------------------
  Python                     3.12+
  Docker                     Recommended
  Docker Compose             v2
  Zabbix                     7.x
  Q330/PB44 HTTP interface   TCP/6381
  Zabbix Sender protocol     TCP/10051
  Operating System           Linux recommended

Validated development environment:

``` text
Python 3.12.14
Docker 29.1.3
Docker Compose 2.40.3
```

------------------------------------------------------------------------

## 🏗️ Architecture

``` text
                    Zabbix 7 API
                         │
                         │ Device discovery
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

## 🗂️ Project Structure

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

## 🚀 Installation

``` bash
git clone git@github.com:rotoapanta/quanterraProject.git
cd quanterraProject
cp .env.example .env
mkdir -p secrets
```

Store only the Zabbix API token in:

``` text
secrets/zabbix_token
```

Do not add quotes or variable names to this file.

------------------------------------------------------------------------

## ⚙️ Configuration

Main environment variables:

  Variable                     Description
  ---------------------------- ----------------------------------
  `ZABBIX_URL`                 Zabbix API URL
  `ZABBIX_SERVER`              Zabbix Server or Proxy
  `ZABBIX_PORT`                Trapper port, default `10051`
  `ZABBIX_TEMPLATE`            Template used for Q330 discovery
  `COLLECTOR_HOST`             Collector technical host name
  `COLLECTOR_HOST_FILTER`      Optional host rollout filter
  `COLLECTOR_INTERVAL`         Collection interval
  `COLLECTOR_TIMEOUT`          HTTP timeout
  `COLLECTOR_WORKERS`          Concurrent workers
  `COLLECTOR_HEALTH_MAX_AGE`   Maximum health-state age
  `Q330_PORT`                  Q330/PB44 HTTP port

Current default discovery template:

``` text
Template Zabbix Trapper Quanterra
```

Collector host:

``` text
Monitoring Data Collector
```

------------------------------------------------------------------------

## 📊 Zabbix Templates

| Template | Items | Triggers | Macros |
|----------|------:|---------:|-------:|
| `Template Zabbix Trapper Quanterra` | 48 | 8 | 7 |
| `Monitoring Data Collector Health` | 6 | 2 | 2 |
| **Total** | **54** | **10** | **9** |

Import `templates/quanterra_zabbix7.yaml` through **Data collection → Templates → Import**.

### 📈 Main Zabbix Metrics

| Metric | Key | Unit |
|--------|-----|------|
| Input voltage | `input.voltage` | `V` |
| System temperature | `system.temp` | `°C` |
| Main current | `main.current` | `mA` |
| Satellites used | `sat.used` | — |
| Clock quality | `clock.quality` | `%` |
| Clock phase | `clock.phase` | `us` |
| GPS antenna current | `gps.antenna.current` | `mA` |
| PB44 UPS voltage | `pb44.ups.voltage` | `V` |
| PB44 primary voltage | `pb44.primary.voltage` | `V` |
| PB44 temperature | `pb44.temperature` | `°C` |
| Received throughput | `data.received.bps.minute` | `Bps` |
| Data latency | `data.latency` | `s` |
| Status latency | `status.latency` | `s` |
| Media site 1 capacity | `media.site1.capacity` | `MB` |
| Media site 2 capacity | `media.site2.capacity` | `MB` |
| Total media occupied | `media.total.space.occupied` | `%` |
| Complete Q330 collection | `q330.collect.success` | — |
| Q330 metrics parsed | `q330.collect.metrics` | — |
| Collector heartbeat | `collector.heartbeat` | `unixtime` |
| Collector cycle duration | `collector.cycle.duration` | `s` |
| Failed or incomplete devices | `collector.devices.failed` | — |
| Collector cycle success | `collector.cycle.success` | — |

### 🚨 Zabbix Triggers

| Template | Trigger | Severity |
|----------|---------|----------|
| Q330 | Input voltage low | Warning |
| Q330 | System temperature high | Warning |
| Q330 | Too few satellites | Warning |
| Q330 | Clock quality low | Warning |
| Q330 | Media total space usage 60–80% | Warning |
| Q330 | Media total space usage ≥80% | High |
| Q330 | No collector data | High |
| Q330 | Collection failed or incomplete | Warning |
| Collector | No successful pipeline | High |
| Collector | Devices failed or incomplete | Warning |

------------------------------------------------------------------------

## 💾 Media Storage Monitoring

The collector monitors physical PB44/Q330 media individually and
calculates total storage utilization.

Relevant metrics include:

``` text
media.site1.free.space
media.site2.free.space
media.total.space.occupied
```

Total media occupation is calculated using the actual capacity of each
valid physical media device. This avoids incorrect averaging when
installed media have different capacities. A system with only one valid
physical media site is also supported.

### Storage triggers

``` text
60% ≤ occupied < 80%  → WARNING
occupied ≥ 80%        → HIGH
```

------------------------------------------------------------------------

## ❤️ Collector Health

  Key                          Purpose
  ---------------------------- -------------------------
  `collector.heartbeat`        Last collector activity
  `collector.uptime`           Collector uptime
  `collector.cycle.duration`   Cycle execution time
  `collector.devices.total`    Devices processed
  `collector.devices.failed`   Failed devices
  `collector.cycle.success`    Overall cycle status

Health template: `Monitoring Data Collector Health`.

------------------------------------------------------------------------

## 🔐 Allowed Hosts

Zabbix trapper items use `{$COLLECTOR.ALLOWED_HOSTS}`. This value must
match the source IP or network actually observed by the Zabbix
Server/Proxy.

The current YAML default is:

``` text
172.22.0.0/16
```

Production deployments should restrict this value to the required source
address or network.

------------------------------------------------------------------------

## 📝 Logging

The collector uses Python logging and writes runtime information to
stdout/stderr and the configured log file. Log rotation is supported.

``` text
logs/collector.log
/app/logs/collector.log
```

Docker Compose persists application logs through the `collector_logs`
volume.

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

Stop with:

``` bash
docker compose down
```

------------------------------------------------------------------------

## 🧪 Tests

``` bash
docker compose run --rm \
  --no-deps \
  --entrypoint python \
  -v "$PWD:/src:ro" \
  -w /src \
  collector \
  -m unittest discover -s tests -v
```

Current validated result:

``` text
Ran 43 tests
OK
```

------------------------------------------------------------------------

## 📦 Dependencies

``` text
requests==2.32.5
zabbix_utils==2.0.4
PyYAML==6.0.2
```

------------------------------------------------------------------------

## 🔒 Security

-   Non-root container user.
-   Read-only root filesystem.
-   Dropped Linux capabilities.
-   `no-new-privileges`.
-   Docker secret for the Zabbix API token.
-   No published application ports.
-   Temporary `/tmp` filesystem.
-   `.env` and `secrets/` excluded from Git.

Never commit the Zabbix API token or production `.env` file.

------------------------------------------------------------------------

## 🔍 Main Data Flow

``` text
Zabbix API
    │
    ▼
Discover Q330 hosts
    │
    ▼
Query HTTP/6381
    │
    ▼
Parse Q330/PB44 telemetry
    │
    ▼
Calculate derived metrics
    │
    ▼
Zabbix Sender
    │
    ▼
Zabbix Server :10051
```

------------------------------------------------------------------------

## 💬 Feedback / Support

robertocarlos.toapanta@gmail.com

## 👥 Author

-   [@rotoapanta](https://github.com/rotoapanta)

------------------------------------------------------------------------

## 🔗 Links

[![GitHub](https://img.shields.io/badge/GitHub-rotoapanta-181717?style=for-the-badge&logo=github)](https://github.com/rotoapanta)

[![LinkedIn](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/roberto-carlos-toapanta-g/)