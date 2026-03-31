# Awaaz

India's roads speak. Now anyone can listen.

## What is this

Awaaz is a self-hostable platform for reporting and publishing road incidents in India. Anyone can submit an incident from a web UI, other users can confirm it, and the system publishes the incident feed to public URLs.

In practice, this is a response to the Waze/Google problem. Every incident that Indian drivers report goes into Google's servers and never comes back out, which means open navigation apps cannot access the data. Awaaz is the open alternative, built so any navigation app or routing engine can consume the same incident feed.

## How it works

The reporting platform is a Django web app where people can drop a pin and describe what is happening on the road. Reports appear immediately as pending or active based on user role, other users can confirm them, and they auto-expire when they are no longer relevant.

The open feed is the publishing layer. Active incidents are serialized as CIFS XML and exposed at public URLs so consumers can poll them over HTTP without an API key.

For readers who do not know CIFS: Closure and Incident Feed Specification is Waze’s open XML format for describing incidents in partner feeds.

## Why we built this

I got tired of seeing useful incident reports disappear into a single closed ecosystem. On Indian roads, the “in the moment” information matters, and it is frustrating when people share it but it never reaches the navigation app of the driver who needs it next.

The data is not the hard part. The hard part is access, and access needs to stay open if we want community and offline navigation tools to participate. That is why I built Awaaz around open feeds and simple self-hosting.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 5, Django REST Framework, GeoDjango |
| Database | PostgreSQL + PostGIS |
| Maps | MapLibre GL JS (via CDN) |
| Feed format | CIFS XML (generated with Python) |
| Background tasks | Celery + Redis (auto-expiry) |
| Mobile consumer | OsmAnd consumer app integration (Android, Java) |
| Containerisation | Docker + docker-compose |
| License | AGPL-3.0-or-later |

## Running it locally

Prerequisites:
Docker, docker-compose, Git, and Android Studio for the OsmAnd plugin.

Step 1 -- Clone the repo

```bash
git clone https://github.com/ndstab/awaaz.git
cd awaaz
```

Step 2 -- Copy the env file

```bash
cp .env.example .env
```

Edit `.env` to set at least the database connection and `SECRET_KEY`. The defaults in this project assume PostGIS is running in the `db` container and Redis is running in the `redis` container.

Step 3 -- Start everything

```bash
docker-compose up --build
```

Step 4 -- Run migrations

```bash
docker-compose exec web python manage.py migrate
```

Step 5 -- Create a superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Step 6 -- Visit http://localhost:8000

```text
http://localhost:8000
```

To create an AUTHORITY account, go to the admin panel and update the user:

```text
/admin
```

Change `role` from `CIVILIAN` to `AUTHORITY` and set `verified=true`.

## Feed endpoints

The feed is public CIFS XML. It only includes incidents that are currently active.

```text
http://localhost:8000/feed/all/
http://localhost:8000/feed/city/<city-slug>/
http://localhost:8000/feed/state/<state-slug>/
```

Example output looks like this:

```xml
<incidents>
  <incident id="...uuid..." creationtime="2026-03-01T10:30:00+05:30" updatetime="2026-03-01T10:30:00+05:30">
    <type>ACCIDENT</type>
    <severity>HIGH</severity>
    <location>
      <street>NH48</street>
      <polyline>12.9716,77.5946</polyline>
    </location>
    <active>true</active>
  </incident>
</incidents>
```

## API reference

```text
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/refresh/

GET /api/v1/incidents/
POST /api/v1/incidents/
GET /api/v1/incidents/<id>/
POST /api/v1/incidents/<id>/confirm/
POST /api/v1/incidents/<id>/resolve/

GET /api/v1/feed/all/
GET /api/v1/feed/city/<slug>/
GET /api/v1/feed/state/<slug>/
```

## OsmAND plugin

Open `osmand-plugin/` in Android Studio, build, and run it on an emulator or a device. In the OsmAnd app, open the Awaaz incidents (feed) screen and use the feed URL.

If you are running the emulator, the default is set to:

```text
http://10.0.2.2:8000/feed/all/
```

## Contributing

This project is young. If you hit bugs, send issues, and if you have improvements, open pull requests. I will prioritize fixes that improve the end to end flow: report, confirm, publish feed, and consume the feed.

Issue tracker: https://github.com/ndstab/awaaz/issues

## License

AGPL-3.0. If someone runs a hosted version of Awaaz, the AGPL requires them to keep their changes open and publish the source code back to users.