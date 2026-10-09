"""Upload dist/wiki/*.wiki to MediaWiki (Miraheze) using a BotPassword."""
import glob, os, mwclient
from urllib.parse import urlparse

u = urlparse(os.environ["MEDIAWIKI_URL"])           # e.g. https://ijc.miraheze.org/w/api.php
path = u.path.rsplit("api.php", 1)[0] or "/w/"
site = mwclient.Site(u.netloc, path=path, scheme=u.scheme)
site.login(os.environ["MEDIAWIKI_USER"], os.environ["MEDIAWIKI_PASSWORD"])

for f in sorted(glob.glob("dist/wiki/*.wiki")):
    name = os.path.basename(f)[:-5]
    title = "IJC Index" if name == "IJC_Index" else name.replace("IJC_", "IJC:", 1)
    text = open(f, encoding="utf-8").read()
    p = site.pages[title]
    if p.text() != text:
        p.edit(text, summary="Automated sync from GitHub")
        print("updated", title)
