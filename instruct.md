# Awaaz -- High Level Design (HLD)

> Written: March 2026 | FOSSHack 2026
> Status: Pre-coding design document. Do not begin writing production code until this is signed off.

---

## 1. What We Are Building (One Paragraph)

Awaaz is a two-sided system. On one side, humans submit road incidents through a
web app. On the other side, navigation apps and routing engines pull those incidents
through a standardized open feed. The database in the middle stores incidents,
handles deduplication, manages confidence scoring, and auto-expires stale reports.
No proprietary APIs anywhere. Fully self-hostable.

---

## 2. System Architecture (HLD Overview)

```
                         REPORTERS
              (Civilians, Traffic Police, Authorities)
                              |
                              | HTTPS (submit incident)
                              v
                    +-------------------+
                    |   Django Backend  |
                    |   (REST API)      |
                    |                  |
                    |  - Auth          |
                    |  - Incident API  |
                    |  - Feed API      |
                    |  - Admin panel   |
                    +--------+---------+
                             |
                             | ORM (GeoDjango)
                             v
                    +-------------------+
                    | PostgreSQL        |
                    | + PostGIS         |
                    |                  |
                    | incidents        |
                    | users            |
                    | confirmations    |
                    | feed_subscriptions|
                    +-------------------+
                             |
               +-------------+-------------+
               |                           |
               v                           v
    +-------------------+       +-------------------+
    |  MapLibre Frontend|       |  CIFS Feed Layer  |
    |  (Web App)        |       |  /feed/city/<slug>|
    |                  |       |  /feed/state/<slug>|
    |  - Submit form   |       |                   |
    |  - Live map view |       |  Valid CIFS XML    |
    |  - Confirm reports|      |  output            |
    +-------------------+       +--------+----------+
                                         |
                                         | HTTP poll / WebSub
                                         v
                              +-------------------+
                              |  CONSUMERS        |
                              |                  |
                              | - OsmAND plugin  |
                              | - Any nav app    |
                              | - OSRM           |
                              | - Custom scripts |
                              +-------------------+
```

---

## 3. Components in Detail

### 3.1 Django Backend

The brain of the system. Handles all business logic.

**Responsibilities:**
- User registration and login (civilians vs authority accounts)
- Receiving incident submissions
- Running spatial deduplication (are two reports the same incident?)
- Updating confidence scores as confirmations come in
- Auto-expiring incidents based on type-specific TTLs
- Serving the CIFS feed endpoints
- Serving the REST API for the frontend

**Framework choices:**
- Django 5.x (stable, well-documented, GeoDjango built in)
- Django REST Framework (DRF) for the API layer
- GeoDjango (Django's built-in GIS extension, works with PostGIS natively)
- Simple JWT for auth tokens
- Celery + Redis for background tasks (auto-expiry, deduplication jobs)

**Why Django and not FastAPI or something lighter?**
GeoDjango. It gives us PostGIS integration, spatial querysets, and admin panel
for free. The overhead is worth it. FastAPI would require wiring all of that
manually.

---

### 3.2 PostgreSQL + PostGIS

The database. PostGIS is a PostgreSQL extension that turns it into a spatial
database -- it understands coordinates, distances, and geographic shapes natively.

**Why PostGIS and not just storing lat/lng as floats?**
Because with float columns, "find all incidents within 5km of this point" is a
slow, hacky calculation done in Python. With PostGIS, it's a single indexed SQL
query that runs in milliseconds even with 100,000 incidents in the table.

**Key spatial operations we will use:**
- `ST_DWithin(geom, point, distance)` -- find incidents near a location
- `ST_Distance(geom1, geom2)` -- calculate distance between two incidents
  (used for deduplication)
- `ST_MakePoint(lng, lat)` -- construct a geometry from coordinates
- Spatial indexes (GIST) on the incident location column

---

### 3.3 MapLibre Frontend

The web app that humans interact with.

**Why MapLibre and not Leaflet or Google Maps?**
MapLibre GL JS is fully open source, renders vector tiles smoothly, and has zero
Google dependency. Leaflet is fine but older and raster-tile based. Google Maps
is a non-starter for this project philosophically.

**Tile source:**
OpenStreetMap tiles served via a free OSM tile server. No API key needed.

**Pages:**
- `/` -- Live map showing all active incidents
- `/report` -- Incident submission form with map location picker
- `/login` and `/register` -- Auth pages
- `/incident/<id>` -- Individual incident detail page
- `/admin` -- Django admin (authority and admin users only)

**Frontend approach:**
Server-side rendered Django templates with MapLibre loaded via CDN. No React,
no build step, no Node dependency. This keeps the project simple and deployable
anywhere. JavaScript only where the map interaction needs it.

---

### 3.4 CIFS Feed Layer

This is the technically interesting part that separates Awaaz from a basic
reporting app.

**What is CIFS?**
Closure and Incident Feed Specification. It is the open XML standard Waze
developed to describe road incidents. It is documented publicly. Any app that
implements a CIFS parser can consume our feed with zero custom integration.

**Feed endpoints:**
```
GET /feed/city/<city-slug>/    -- all active incidents in a city
GET /feed/state/<state-slug>/  -- all active incidents in a state
GET /feed/all/                 -- everything (for testing)
```

**What the CIFS XML looks like (simplified):**
```xml
<incident id="awaaz-1234" creationtime="2026-03-01T10:30:00Z"
          updatetime="2026-03-01T10:30:00Z">
  <updatetime>2026-03-01T10:30:00Z</updatetime>
  <type>ACCIDENT</type>
  <severity>MAJOR</severity>
  <location>
    <street>NH48</street>
    <polyline>12.9716,77.5946</polyline>
  </location>
  <active>true</active>
</incident>
```

**Feed generation:**
A Django view queries PostGIS for all active incidents in the relevant
geographic boundary and serializes them to CIFS XML using Python's built-in
`xml.etree.ElementTree`. No third-party XML libraries needed.

**Feed update strategy:**
Feeds are generated on request (not pre-cached) for simplicity during the
hackathon. A production system would cache and invalidate, but that is
scope creep for March.

---

### 3.5 OsmAND Plugin (Proof of Concept)

A minimal Android plugin for OsmAND that:
1. Lets the user enter an Awaaz feed URL in plugin settings
2. Polls the feed every 5 minutes in a background service
3. Parses the CIFS XML response
4. Renders incident icons on the OsmAND map at the correct coordinates
5. Shows a toast notification when you're within 2km of an active incident

**Language:** Java (OsmAND's codebase is Java, Kotlin interop is possible but
adds complexity)

**This is the hardest single piece of the project.** OsmAND's plugin API is
not well documented. Plan at least 5 days for this in Week 4.

**Fallback:** If the OsmAND plugin proves too time-consuming, build a simple
Python script that polls the feed and prints incident summaries to the terminal.
This still proves the feed works. The OsmAND plugin is the preferred demo but
not worth sacrificing the feed quality for.

---

## 4. Data Models

### 4.1 User

```
User
----
id              UUID (primary key)
email           string (unique)
username        string
password_hash   string
role            enum [CIVILIAN, AUTHORITY, ADMIN]
verified        boolean (authorities need manual verification)
created_at      datetime
```

Roles explained:
- CIVILIAN -- anyone who signs up. Reports go through confidence scoring.
- AUTHORITY -- traffic police, NHAI, state transport dept. Reports go live
  immediately, bypass confidence threshold.
- ADMIN -- can verify authority accounts, moderate incidents.

---

### 4.2 Incident

```
Incident
--------
id              UUID (primary key)
reporter        FK -> User
type            enum [ACCIDENT, FLOOD, ROAD_CLOSURE, CONSTRUCTION,
                      POLICE_NAKA, PROTEST, HAZARD, OTHER]
severity        enum [LOW, MEDIUM, HIGH, CRITICAL]
description     text (optional, max 500 chars)
location        geometry(Point, 4326)   <-- PostGIS spatial column
address_text    string (reverse geocoded, stored for display)
city            string
state           string
photo           file path (optional)
status          enum [PENDING, ACTIVE, RESOLVED, EXPIRED]
confidence      integer (0-100, starts at 20 for civilian, 100 for authority)
confirmation_count  integer (default 0)
reported_at     datetime
expires_at      datetime (calculated at submission based on type TTL)
resolved_at     datetime (null until resolved)
```

**Type TTL defaults (how long before auto-expiry):**
```
ACCIDENT        3 hours
FLOOD           6 hours
ROAD_CLOSURE    24 hours
CONSTRUCTION    7 days
POLICE_NAKA     2 hours
PROTEST         4 hours
HAZARD          12 hours
OTHER           6 hours
```

**Confidence threshold for going ACTIVE:**
An incident needs confidence >= 50 to appear on the public map and feed.
A civilian report starts at 20. Each confirmation from a different user within
5km of the incident adds 15 points. An authority report starts at 100 (immediately
active).

---

### 4.3 Confirmation

```
Confirmation
------------
id          UUID
incident    FK -> Incident
confirmer   FK -> User
location    geometry(Point, 4326)  <-- where the confirmer was when they confirmed
confirmed_at datetime
```

We store the confirmer's location to validate they were actually near the incident
(within 5km). This prevents remote spam confirmations.

---

### 4.4 FeedSubscription (optional, for WebSub later)

```
FeedSubscription
----------------
id              UUID
feed_type       enum [CITY, STATE, ALL]
feed_slug       string (e.g. "bangalore", "karnataka")
callback_url    string
verified        boolean
created_at      datetime
```

This is for WebSub (push notifications to subscribers when feed updates).
Implement this only if Week 3 goes smoothly. Not required for a working demo.

---

## 5. API Design

All API endpoints are under `/api/v1/`.
Auth endpoints use Simple JWT (access token + refresh token).

### Auth
```
POST   /api/v1/auth/register/        create account
POST   /api/v1/auth/login/           get tokens
POST   /api/v1/auth/refresh/         refresh access token
```

### Incidents
```
GET    /api/v1/incidents/            list active incidents (with bbox filter)
POST   /api/v1/incidents/            submit new incident (auth required)
GET    /api/v1/incidents/<id>/       get single incident
POST   /api/v1/incidents/<id>/confirm/   confirm an incident (auth required)
POST   /api/v1/incidents/<id>/resolve/   mark resolved (authority/admin only)
```

**Key query params for GET /api/v1/incidents/:**
```
?bbox=12.8,77.4,13.1,77.7     bounding box (south,west,north,east)
?city=bangalore                filter by city
?state=karnataka               filter by state
?type=ACCIDENT,FLOOD           filter by incident type
?severity=HIGH,CRITICAL        filter by severity
```

### Feeds (not under /api, these are public)
```
GET    /feed/city/<slug>/            CIFS XML for a city
GET    /feed/state/<slug>/           CIFS XML for a state
GET    /feed/all/                    CIFS XML for everything
```

### Admin (Django admin panel)
```
/admin/     Django's built-in admin, customized for incident moderation
            and authority account verification
```

---

## 6. Spatial Deduplication Logic

When a new civilian report comes in, before saving it, run this check:

```
1. Query PostGIS for any ACTIVE or PENDING incidents of the same type
   within 300 metres of the submitted location, reported in the last 2 hours.

2. If a match is found:
   - Do not create a new incident
   - Instead, add a Confirmation record to the existing incident
   - Recalculate its confidence score
   - Return the existing incident ID to the user with a message:
     "Someone already reported this. Your confirmation has been added."

3. If no match is found:
   - Create a new Incident record
   - Set confidence to 20 (civilian) or 100 (authority)
   - Set status to PENDING if confidence < 50, else ACTIVE
```

The 300 metre radius and 2 hour window are configurable constants in settings.py.

---

## 7. Auto-Expiry System

A Celery beat task runs every 15 minutes and does the following:

```
1. Query for all incidents where status = ACTIVE and expires_at < now()
   --> Mark them EXPIRED

2. Query for all incidents where status = PENDING and reported_at < (now - 1 hour)
   --> Mark them EXPIRED (nobody confirmed it, probably false alarm)

3. Query for all incidents where status = ACTIVE and last confirmation > 2x TTL ago
   --> Mark them EXPIRED (incident is stale, nobody confirming it anymore)
```

Redis is required for Celery. This is a simple setup with docker-compose.

---

## 8. Tech Stack Summary

| Layer              | Technology                    | Why                                      |
|--------------------|-------------------------------|------------------------------------------|
| Backend framework  | Django 5.x + GeoDjango        | PostGIS integration built in             |
| API layer          | Django REST Framework         | Standard, well documented                |
| Auth               | Simple JWT                    | Stateless, works well with DRF           |
| Database           | PostgreSQL 16 + PostGIS 3.4   | Spatial queries, production grade        |
| Background tasks   | Celery + Redis                | Auto-expiry, async jobs                  |
| Frontend maps      | MapLibre GL JS (CDN)          | Open source, vector tiles, no Google     |
| Map tiles          | OSM tile server               | Free, no API key                         |
| Feed format        | CIFS XML (built-in xml lib)   | Open standard, Waze-compatible           |
| OsmAND plugin      | Java                          | OsmAND's native language                 |
| Containerization   | Docker + docker-compose       | Anyone can run it in one command         |
| License            | AGPL-3.0                      | Changes must stay open                   |

---

## 9. Prerequisites (What You Need to Know Before Coding)

**Must know before Day 1:**
- Django basics (models, views, URLs, admin)
- REST APIs and how DRF serializers work
- Basic SQL

**Must learn in Week 1 (before it blocks you):**
- GeoDjango setup (installing PostGIS, configuring DATABASES in settings.py
  with ENGINE = 'django.contrib.gis.db.backends.postgis')
- PostGIS geometry field types (PointField, what SRID 4326 means)
- ST_DWithin and ST_Distance -- just these two spatial functions cover 90%
  of what we need
- Docker and docker-compose basics (to run PostGIS locally without
  installing it on your machine)

**Can learn in Week 3 when you get there:**
- CIFS XML spec (read the Waze documentation, it is publicly available)
- xml.etree.ElementTree in Python (straightforward)

**Can learn in Week 4:**
- OsmAND plugin SDK basics
- Android background services (for the polling job in the plugin)

**You do NOT need:**
- React or any frontend framework
- GraphQL
- Kubernetes or anything cloud-native
- Any paid API keys

---

## 10. Folder Structure (Proposed)

```
awaaz/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
├── awaaz/                      # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── incidents/                  # Core app
│   ├── models.py               # Incident, Confirmation
│   ├── serializers.py
│   ├── views.py                # API views
│   ├── urls.py
│   ├── tasks.py                # Celery auto-expiry tasks
│   └── feed.py                 # CIFS XML generation
├── users/                      # Auth app
│   ├── models.py               # Custom User model
│   ├── serializers.py
│   └── views.py
├── frontend/                   # Django templates + static
│   ├── templates/
│   │   ├── base.html
│   │   ├── map.html            # Main map view
│   │   ├── report.html         # Submit form
│   │   └── incident.html       # Detail page
│   └── static/
│       ├── css/
│       └── js/
│           └── map.js          # MapLibre initialization
└── osmand-plugin/              # Separate Android project
    └── src/
```

---

## 11. What We Are Not Building (Scope Boundaries)

Explicitly out of scope for March, to avoid scope creep:

- Mobile app (the OsmAND plugin is enough mobile surface area)
- Push notifications to users (WebSub is optional, polling is fine)
- Real-time WebSocket updates on the map (HTTP polling every 30s is fine)
- Route-aware incident filtering ("only show incidents on my current route")
- SMS reporting (for non-smartphone users, good idea, post-hackathon)
- Multilingual UI (English only for now)
- Traffic speed data (incidents only, not congestion heatmaps)
- Payments, premium tiers, anything monetization related

---

## 12. Definition of Done (for March 31)

The project is complete and submittable when:

- [ ] A civilian can register, submit an incident with a location, and see it
      on the map after reaching confidence threshold
- [ ] An authority account bypasses confidence and goes live immediately
- [ ] Spatial deduplication correctly merges nearby duplicate reports
- [ ] Auto-expiry correctly marks stale incidents as expired
- [ ] `/feed/city/bangalore/` returns valid CIFS XML with active incidents
- [ ] The OsmAND plugin (or fallback demo script) successfully reads the feed
      and displays an incident
- [ ] docker-compose up brings the entire system up in one command
- [ ] README explains how to self-host it
- [ ] Demo video shows the full flow: submit incident -> appears on map ->
      appears in CIFS feed -> OsmAND shows it

---

*This document is the source of truth for what Awaaz is. If a feature is not
in this document, it is not in scope for March.*