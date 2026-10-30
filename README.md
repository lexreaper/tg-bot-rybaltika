# Manufaktura Network Hub API

Backend API for the bar network hub: bar website links, events, vacancies, and
loyalty-program information.

## Configuration

Set the database variables already used by the project in `.env`. Also set
`ADMIN_API_TOKEN` to a random secret of at least 32 characters. Keep this value
private; it grants access to all administrative operations.

The database schema is upgraded to the latest Alembic revision when the
application starts.

## Public endpoints

- `GET /bars` — published bar links.
- `GET /events` — published upcoming events. Supports `bar_id`,
  `upcoming_only`, `offset`, and `limit` query parameters.
- `GET /events/{event_id}` — one published event.
- `GET /vacancies` — published vacancies.
- `GET /loyalty` — published loyalty-program information.

List endpoints support `offset` and `limit` (maximum 100).

## Administrative endpoints

All `/admin` endpoints require
`Authorization: Bearer <ADMIN_API_TOKEN>`. For each resource below, the API
provides `GET` collection/item, `POST` collection, `PATCH` item, and `DELETE`
item operations:

- `/admin/bars`
- `/admin/events`
- `/admin/vacancies`
- `/admin/loyalty`

Administrative collection endpoints support `offset` and `limit`; records are
created as drafts by default and become publicly readable when
`is_published` is set to `true`.

Request validation failures return `422`, missing records return `404`,
duplicate keys or invalid references return `409`, and missing/invalid admin
token configuration returns `503`; missing or invalid bearer credentials
return `401`.