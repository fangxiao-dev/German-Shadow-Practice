# Shadow Dashboard

Local read-only dashboard for browsing committed shadow assets in a compact table.

## Files

- `index.html`: compact local web view
- `styles.css`: dashboard styling
- `app.js`: client-side rendering logic
- `data/dashboard-data.json`: generated view data

The dashboard emphasizes:
- latest committed items at the top
- a transcript sentence for each item instead of raw YAML fields
- subordinate `collocation` hooks rendered beneath the main target when present
- weekly grouped archive below, collapsed by default

## Usage

1. Rebuild dashboard data:

   ```powershell
   python scripts\build_shadow_dashboard.py
   ```

2. Start a local server from the project root:

   ```powershell
   python -m http.server 4173 --directory dashboard
   ```

3. Open:

   [http://localhost:4173](http://localhost:4173)

## One-click launcher

Run the launcher script to rebuild data, start the local server, and open the dashboard in one step:

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\start_shadow_dashboard.ps1
```

For verification or headless use, skip opening the browser:

```powershell
pwsh -ExecutionPolicy Bypass -File scripts\start_shadow_dashboard.ps1 -NoOpen
```

The page is read-only. Edit the YAML files through the workflow, then rerun the build script to refresh the dashboard.

## Commit workflow

When you run:

```powershell
python scripts\shadow_commit.py --session shadow_sessions\YYYY-MM-DD-HHMM.md
```

the commit step now opens the dashboard automatically by default after writing durable state.

- If the local dashboard server is not running, the commit step starts it and opens the page.
- If the server is already running on `http://localhost:4173`, the commit step reuses it and opens the refreshed versioned URL.
- Use `--no-dashboard` to skip dashboard follow-up.
- Use `--no-open` to refresh/start the dashboard flow without opening the browser.
