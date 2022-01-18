<p align="center">
  <pre >
     _______           __       __ __     __ ________
    |       \         |  \     /  \  \   |  \        \
    | ▓▓▓▓▓▓▓\ ______ | ▓▓\   /  ▓▓ ▓▓   | ▓▓\▓▓▓▓▓▓▓▓
    | ▓▓__/ ▓▓/      \| ▓▓▓\ /  ▓▓▓ ▓▓   | ▓▓  | ▓▓
    | ▓▓    ▓▓  ▓▓▓▓▓▓\ ▓▓▓▓\  ▓▓▓▓\▓▓\ /  ▓▓  | ▓▓
    | ▓▓▓▓▓▓▓| ▓▓  | ▓▓ ▓▓\▓▓ ▓▓ ▓▓ \▓▓\  ▓▓   | ▓▓
    | ▓▓     | ▓▓__| ▓▓ ▓▓ \▓▓▓| ▓▓  \▓▓ ▓▓    | ▓▓
    | ▓▓      \▓▓    ▓▓ ▓▓  \▓ | ▓▓   \▓▓▓     | ▓▓
     \▓▓      _\▓▓▓▓▓▓▓\▓▓      \▓▓    \▓       \▓▓
             |  \__| ▓▓
              \▓▓    ▓▓
                \▓▓▓▓▓▓
  </pre>
  <p align="center">A TiMVT replica using Starlite framework.</p>
</p>

<p align="center">
  <a href="https://github.com/developmentseed/pg_mvt/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/pg_mvt/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/developmentseed/pg_mvt" target="_blank">
      <img src="https://codecov.io/gh/developmentseed/pg_mvt/branch/master/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://github.com/developmentseed/pg_mvt/blob/master/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/pg_mvt.svg" alt="License">

  </a>
</p>

---

**Source Code**: <a href="https://github.com/developmentseed/pg_mvt" target="_blank">https://github.com/developmentseed/pg_mvt</a>

---

`pg_mvt` is a replica of [TiMVT](https://github.com/developmentseed/timvt) but using [Starlite](https://github.com/starlite-api/starlite) framework instead of FastAPI.


## Install

```bash
$ git clone https://github.com/developmentseed/pg_mvt.git
$ cd pg_mvt
$ python -m pip install -e .
```

## Launch

```bash
$ pip install uvicorn

$ uvicorn pg_mvt.main:app
```

## PostGIS/Postgres

`pg_mvt` rely mostly on [`ST_AsMVT`](https://postgis.net/docs/ST_AsMVT.html) function and will need PostGIS >= 2.5.

If you want more info about `ST_AsMVT` function or on the subject of creating Vector Tile from PostGIS, please read this great article from Paul Ramsey: https://info.crunchydata.com/blog/dynamic-vector-tiles-from-postgis

### Configuration

To be able to create Vector Tile, the application will need access to the PostGIS database. `pg_mvt` uses [starlette](https://www.starlette.io/config/)'s configuration pattern which make use of environment variable and/or `.env` file to pass variable to the application.

Example of `.env` file can be found in [.env.example](https://github.com/developmentseed/pg_mvt/blob/master/.env.example)

```
# you need define the DATABASE_URL directly
PG_MVT_DATABASE_URL=postgresql://username:password@0.0.0.0:5432/postgis
```

## Performances

```
$ siege --file benchmark/urls.txt -b -c 20 -r 100
# pg_mvt (starlite)
Transactions:                   2000 hits
Availability:                 100.00 %
Elapsed time:                   5.03 secs
Data transferred:               7.00 MB
Response time:                  0.04 secs
Transaction rate:             397.61 trans/sec
Throughput:                     1.39 MB/sec
Concurrency:                   16.97
Successful transactions:        2000
Failed transactions:               0
Longest transaction:            0.19
Shortest transaction:           0.01

# timvt (fastapi)
Transactions:                   2000 hits
Availability:                 100.00 %
Elapsed time:                   5.12 secs
Data transferred:               6.98 MB
Response time:                  0.04 secs
Transaction rate:             390.62 trans/sec
Throughput:                     1.36 MB/sec
Concurrency:                   16.84
Successful transactions:        2000
Failed transactions:               0
Longest transaction:            0.19
Shortest transaction:           0.01
```

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/pg_mvt/blob/master/CONTRIBUTING.md)

## License

See [LICENSE](https://github.com/developmentseed/pg_mvt/blob/master/LICENSE)

## Authors

Created by [Development Seed](<http://developmentseed.org>)

## Changes

See [CHANGES.md](https://github.com/developmentseed/pg_mvt/blob/master/CHANGES.md).

