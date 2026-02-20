# Heat Acclimation Calendar

A simple Flask app that generates heat adaptation session calendars (dry sauna and/or hot tub) based on the [TrainRight Ultrarunners' Heat Acclimation Cheat Sheet](https://trainright.com/ultrarunners-heat-acclimation-cheat-sheet/) (Jason Koop / CTS).

- **Protocol 1 (Single exposure):** 10 consecutive days of heat sessions ending one day before the race.
- **Protocol 2 (Repeated exposure):** First bout ~6 weeks out (10 days), maintenance every 3 days, then a second bout in the final week (7 days).

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001), enter your race date, and click **Generate calendars**.

## Static version (no server)

The `static/` directory contains a single-file version that runs entirely in the browser. Open `static/index.html` directly in a browser, or serve it with any static file server.

## GitHub Pages

The repo includes `index.html` at the root for GitHub Pages. After pushing:

1. Create a new repo on GitHub (e.g. `heat-training`)
2. Add the remote and push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/heat-training.git
   git branch -M main
   git push -u origin main
   ```
3. In the repo: **Settings** → **Pages** → **Build and deployment**
4. Set **Source** to **Deploy from a branch**
5. Branch: `main`, folder: `/ (root)` → Save

The app will be live at `https://YOUR_USERNAME.github.io/heat-training/`
