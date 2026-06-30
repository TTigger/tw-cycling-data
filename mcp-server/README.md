# tw-cycling-data MCP server

讓 MCP 用戶端(Claude 等)查詢台灣公路車賽公開資料(去識別化)。即時讀線上 v1 API。

## 執行

```bash
uvx --from git+https://github.com/TTigger/tw-cycling-data#subdirectory=mcp-server tw-cycling-data-mcp
```

或本機開發:
```bash
cd mcp-server && uv run tw-cycling-data-mcp
```

預設讀 `https://tw-cycling-data.vercel.app/data/v1`;以 `TWCD_API_BASE` 覆寫(例如指向本機建置)。

## Tools

`dataset_overview`、`search_athletes(query, limit)`、`get_athlete(athlete_id)`、`list_races(year?, race_type?, query?, limit)`、`get_race(race_key)`、`get_team(team_id)`。

## 在 Claude Desktop 設定

```json
{
  "mcpServers": {
    "tw-cycling-data": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/TTigger/tw-cycling-data#subdirectory=mcp-server", "tw-cycling-data-mcp"]
    }
  }
}
```

資料授權 CC BY 4.0;請標註來源。
