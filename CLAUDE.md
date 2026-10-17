# Tengis Ulzii — Portfolio

Single-file portfolio site: everything (HTML, CSS, JS, base64 photo) lives in `index.html`.

- Style: brutalist — black / white / electric blue (#3B2BFF), hard edges, boxed mono buttons.
- Fonts: Unbounded (display), Geist, Geist Mono via Google Fonts.
- Themes: `data-theme="black"` (default) and `data-theme="blue"`.
- Intro reel (`#intro`, canvas): dusk valley photo with birds (embedded base64 WebP, 1672×941); each bird is keyed out and painted out of the photo, then flies on its own. Opens close on the flock, widens to the full valley, then its canvas moves into `#bg` and keeps running behind the hero only (`#bg` is absolute at the top and scrolls away). Skippable; reduced motion shows a still.
- Views: home (hero, now strip, work, about, contact), projects list, case study pages — switched by JS via `data-go` and the URL hash.
- Libraries: GSAP + ScrollTrigger, Lenis smooth scroll (loaded from CDN).
- Projects: Tino, Garage, Pinecone, Cheepah, Playmo, TDB, MKaraoke.

Preview: open `index.html` in a browser, or run `npx serve .`

Live at https://cean.space — GitHub Pages from `Ceanwaver/tengis-portfolio` (branch `main`, root). Pushing to `main` redeploys in about a minute. DNS is at Spaceship (4 A records to GitHub Pages + `www` CNAME to `ceanwaver.github.io`).

Originally published as a Claude artifact: https://claude.ai/artifact/R6kGEV1E9qfL7qCxUtBPBP
