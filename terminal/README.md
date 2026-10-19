# Terminal intro

The animation on my profile is `assets/whoami.svg`, generated from `config.json`.

Edit `config.json`, then run:

    python3 terminal/build.py

- `"value"` is a static row.
- `"values"` is a rotating row: each loop of the animation shows the next entry (shorter lists repeat).
- `"color": "green"` highlights a row.
- Lines that are too long are handled automatically; the terminal widens to fit.
