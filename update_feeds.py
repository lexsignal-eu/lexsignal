#!/usr/bin/env python3
"""LexSignal: collect public RSS/Atom summaries from named official sources.

Snapshots are automatically classified and unreviewed; no legal validation is implied.
No external dependencies. Run: python update_feeds.py
"""
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

SOURCES = [
  ("ESMA", "https://www.esma.europa.eu/rss.xml"),
  ("EDPB", "https://www.edpb.europa.eu/rss.xml_en"),
  ("European Commission", "https://commission.europa.eu/news/feed_en"),
  ("Central Bank of Ireland", "https://www.centralbank.ie/feeds/news-media-feed"),
]
KEYWORDS = {
  "fin": ("mica","crypto","financial","bank","payment","investment","securities","aml","laundering","sanction","dora","fintech","insurance","capital market","fund management","supervision"),
  "privacy": ("gdpr","privacy","personal data","data protection","data breach","edpb","cyber","digital services act"),
  "ai": ("artificial intelligence","ai act","ai governance","generative ai","machine learning","algorithmic","foundation model","deepfake"),
}
ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"

def official(url):
    try:
        p=urllib.parse.urlparse(url)
        host=(p.hostname or "").lower()
        return p.scheme=="https" and not p.username and not p.password and (
            host=="europa.eu" or host.endswith(".europa.eu") or host=="centralbank.ie" or host.endswith(".centralbank.ie")
        )
    except ValueError:
        return False

def clean(value, limit=500):
    value=re.sub(r"<[^>]+>"," ", value or "")
    return re.sub(r"\s+"," ",html.unescape(value)).strip()[:limit]

def node(item,*tags):
    for tag in tags:
        child=item.find(tag)
        if child is not None:
            val="".join(child.itertext()).strip()
            if val:
                return val
    return ""

def iso(value):
    if not value: return None
    try: return parsedate_to_datetime(value).date().isoformat()
    except (ValueError,TypeError,IndexError): pass
    try: return datetime.fromisoformat(value.replace("Z","+00:00")).date().isoformat()
    except (ValueError,TypeError): return None

def parse(xml,authority,now):
    root=ET.fromstring(xml)
    entries=root.findall(".//item")
    atom=not bool(entries)
    if atom: entries=root.findall(".//"+ATOM+"entry")
    first=(now-timedelta(days=150)).date().isoformat()
    last=(now+timedelta(days=1)).date().isoformat()
    records=[]
    for item in entries[:120]:
        title=clean(node(item,ATOM+"title" if atom else "title"),200)
        if atom:
            links=[a.attrib.get("href","") for a in item.findall(ATOM+"link")]
            link=next((x for x in links if official(x)),"")
            date=iso(node(item,ATOM+"published",ATOM+"updated"))
            summary=clean(node(item,ATOM+"summary",ATOM+"content"),470)
        else:
            link=node(item,"link")
            date=iso(node(item,"pubDate",DC+"date","date"))
            summary=clean(node(item,"description","{http://purl.org/rss/1.0/modules/content/}encoded"),470)
        if not title or not date or not official(link) or not(first<=date<=last):
            continue
        terms=(title+" "+summary).lower()
        sectors=[sector for sector,keywords in KEYWORDS.items()
                 if any(re.search(r"(?<![a-z])"+re.escape(k)+r"(?![a-z])",terms) for k in keywords)]
        if authority=="EDPB" and "privacy" not in sectors: sectors.append("privacy")
        if not sectors: continue
        category="AI / digital regulation" if "ai" in sectors else "Data protection" if "privacy" in sectors else "Financial regulation"
        kind=("consultation" if re.search("consultation|call for evidence",terms) else
              "enforcement" if re.search("fine|penalty|enforcement",terms) else
              "deadline" if re.search("deadline|takes effect|enters into force",terms) else
              "guidance" if re.search("guideline|guidance|opinion|recommendation|q&a",terms) else "news")
        rid="rss-"+hashlib.sha256((authority+"|"+link.split("#")[0]).encode()).hexdigest()[:16]
        records.append({
          "id":rid,"date":date,"authority":authority,"category":category,"kind":kind,
          "title":title,"summary":summary or "See primary source.",
          "impact":"Automatically collected summary; relevance and applicability have not been checked.",
          "actions":["Verify the original publication and date.","Assess applicability to the client."],
          "url":link,"sectors":sectors,"priority":"unassessed","sourceType":"rss","needsReview":True
        })
    return records

def main():
    now=datetime.now(timezone.utc)
    result={}
    statuses=[]
    successes=0
    for name,url in SOURCES:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"LexSignal/0.2 public source monitoring","Accept":"application/rss+xml,application/atom+xml,text/xml,application/xml,*/*;q=0.5"})
            with urllib.request.urlopen(req,timeout=20) as reply:
                if reply.status!=200: raise ValueError("HTTP "+str(reply.status))
                xml=reply.read(2_000_001)
            if len(xml)>2_000_000: raise ValueError("Feed >2 MB")
            recs=parse(xml,name,now)
            successes+=1
            for rec in recs: result[rec["id"]]=rec
            statuses.append({"authority":name,"url":url,"status":"ok","matched":len(recs)})
            print(name,"OK",len(recs))
        except Exception as e:
            statuses.append({"authority":name,"url":url,"status":"error","message":type(e).__name__+": "+str(e)[:180]})
            print(name,"ERROR",type(e).__name__,str(e)[:180],file=sys.stderr)
    if successes==0:
        print("No feeds succeeded; existing snapshot retained.",file=sys.stderr)
        return 1
    doc={"schema":"lexsignal-snapshot-v1","generatedAt":now.isoformat(timespec="seconds"),
         "disclaimer":"RSS-derived, automatically classified, not fact-checked or legal advice.",
         "sources":statuses,"records":sorted(result.values(),key=lambda r:(r["date"],r["id"]),reverse=True)[:100]}
    dest=Path("data/regulatory_snapshot.json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Snapshot:",len(doc["records"]),"records")
    return 0

if __name__=="__main__": sys.exit(main())
