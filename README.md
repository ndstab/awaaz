# Awaaz

India's roads speak. Now anyone can listen.

## What is this?

Awaaz is an open source platform for reporting and publishing road incidents in India.

Every day, drivers across India run into accidents, floods, police nakas, highway
blockages, broken diversions. Some tweet about it. Some post in WhatsApp groups.
Most just honk and wait. None of this ever reaches the navigation app of the person
driving into the same mess five minutes later.

Waze was supposed to fix this. And it does, kind of. Except Waze is Google. Every
incident an Indian driver reports disappears into Google's servers and never comes
back out. OsmAND can't use it. A student building a routing app for rural roads
can't use it. A state disaster management system can't use it. The data exists,
it's just locked away.

Awaaz is the open alternative.

## How it works

Two parts:

**Reporting platform** -- a web app where anyone (civilians, traffic cops, highway
authorities) can drop a pin and report what's happening on the road. Accidents,
flooding, construction, road closures, whatever. Reports show up live on a map,
other drivers can confirm them, and they auto-expire when no longer relevant.

**Open feed** -- every reported incident gets published as a CIFS feed (the same
open standard Waze uses internally to describe road incidents). City feeds, state
feeds, all at public URLs. Any navigation app or routing engine can subscribe and
pull live Indian road incident data. No API key, no Google, no permission needed.

We're also building a small OsmAND plugin to show the feed working end to end in
a real navigation app.

## Stack

- Django + PostGIS (backend + geospatial queries)
- MapLibre GL JS (maps, zero Google dependency)
- CIFS XML (open incident feed standard)
- OsmAND Plugin SDK / Java (the consumer proof of concept)

## Running locally

*Instructions coming as the project takes shape. Check back in a few days.*

## Project status

Work in progress. Started March 2026 as part of FOSSHack 2026.

Current focus: getting the core incident submission and map rendering working
before moving on to the feed layer.

## Why AGPL?

If someone takes this code and runs a hosted version of Awaaz, their changes
should come back to the commons. That's the whole point of the project.

## Contributing

Too early for external contributions right now but issues and feedback are welcome.
Once the core is stable (roughly mid-March) we'll open it up properly.

## License

AGPL-3.0