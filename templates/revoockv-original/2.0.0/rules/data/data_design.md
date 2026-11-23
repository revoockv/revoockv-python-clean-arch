# Data design — small parts, orchestrated by the repository

A big file is a design problem, not a style problem: it does several jobs that belong in separate classes. The
data layer has a place for each job, and the **repository implementation is the one class that combines them**.

## One job per class

| Job | Class | Lives in | May raise |
|---|---|---|---|
| Talk to **one** external system (an API, a site, a DB, a file store) | `<System><Name>DataSource` | `data/data_sources/` | yes |
| Wrap **one** library or tool (a browser, ffmpeg, a converter, a model runner, the clock) | `<Tool>Service` | `data/services/` | yes |
| Parse / serialize the wire shape (JSON, rows, HTML cards, CLI output) | `<Name>Model.from_dict` / `from_row` / `from_html` … | `data/models/` | yes (bad payload) |
| Combine them: call in order or concurrently, merge, retry, fall back, map to entities, turn errors into `Failure`, log | `<Name>RepositoryImpl` | `data/repositories/` | no — returns `Result` |

- A data source does I/O and returns models. It does not parse markup line by line — it hands the raw payload to a
  model classmethod — and it does not decide what happens when another source fails.
- A service knows nothing about features: `BrowserService.open_page(url)` serves every scraper; the site-specific
  selectors stay in the data source or the model of that site.
- Data sources and services never call each other's siblings to orchestrate; when one needs a service it receives it
  by constructor, but deciding the order of several sources is the repository's job.
- The domain sees none of this: one repository interface, one use case per user interaction
  (`rules/use_cases/use_case_naming.md`).

## Signs a file must be split (linter: `file_size`)

`file_size` fails a file with more than `max_file_lines` non-blank lines (`[lint.params]`, 200 here). Before the
limit, split when a class:

- talks to two systems (two base URLs, a site and a cache) → two data sources;
- sets up a library (browser launch, sessions, retries with backoff, cookies) and also uses it for one site → a
  service for the library, the site stays a data source;
- holds long parsing code (selectors, regexes, field cleanup) next to the requests → `from_<format>` on the model,
  or one model per wire shape;
- loops over several sources, merges or deduplicates them → that is the repository.

## Example: several job boards

```
data/
  services/browser_service.py            BrowserService: one warm Playwright browser, open_page(), close()
  data_sources/vacancy_data_source.py    VacancyDataSource (ABC): search(query, limit) -> list[JobModel]
  data_sources/dou_data_source.py        DouDataSource(VacancyDataSource): HTTP + pagination, cards → JobModel.from_dou_card
  data_sources/robota_data_source.py     RobotaDataSource(VacancyDataSource): uses BrowserService, cards → JobModel.from_robota_card
  models/job_model.py                    JobModel: from_dou_card / from_robota_card / to_entity / from_entity
  repositories/vacancy_repository_impl.py
```

The repository receives every data source (a `tuple[VacancyDataSource, ...]` or one argument per source), runs them
with `asyncio.gather(..., return_exceptions=True)`, keeps what succeeded, logs and reports every failure, and
returns one `Result`. Every source shares one base type, so adding a board is one new class and one line in
`<feature>_di.py`.

In `example/`: `StatisticsRepositoryImpl` combines a data source (`DatabaseStatisticsDataSource`) with a service
(`ClockService`) — `example/src/example_app/features/statistics/data/repositories/statistics_repository_impl.py`.
