# EPM Data: Dunks & Threes API Setup

EPM (Estimated Plus-Minus) is fetched automatically from the dunksandthrees.com REST API.
An API key is required. Once a season is cached, the key is not needed again for that season.

## 1. Get an API key

1. Register at [dunksandthrees.com](https://www.dunksandthrees.com)
2. After registration, the API key is sent to your email.
3. Contact admin@dunksandthrees.com if the key does not arrive.

## 2. Set the environment variable

```bash
export DUNKS_API_KEY=your_key_here
```

Add it to your shell profile (`~/.zshrc` or `~/.bash_profile`) to avoid setting it each session.

## 3. Run the pipeline

```bash
export DUNKS_API_KEY=your_key_here
MPLBACKEND=Agg python3 player_ranking_overview.py
```

On the first run for a season, the pipeline fetches EPM from the API and writes:

```
/Users/justin/code/nba_analysis/cache/epm_2024-25.csv
```

Subsequent runs read from that cache file and skip the network call. To force a re-fetch,
delete the cache file and re-run.

## 4. Columns added to the unified ratings table

| Column | Source field | Description |
|--------|-------------|-------------|
| `EPM`  | `tot`       | Total EPM (offense + defense) |
| `EPM_O`| `off`       | Offensive EPM |
| `EPM_D`| `def`       | Defensive EPM |

## API details

- Endpoint: `GET https://www.dunksandthrees.com/api/v1/season-epm`
- Parameters: `season` (end year, e.g. `2025` for 2024-25), `seasontype` (`2` = regular season)
- Auth header: `Authorization: your_key_here`
- Rate limit: 3 requests per minute for season-level queries
- Full docs: `https://www.dunksandthrees.com/api/v1/documentation`

## Other third-party systems

| System | Status |
|--------|--------|
| RAPTOR (FiveThirtyEight) | Auto-downloads; coverage ended at 2022-23 |
| DARKO DPM | Discontinued; no longer published |
| LEBRON (bball-index.com) | No public API; subscription required |
| ESPN RPM | No public API |
