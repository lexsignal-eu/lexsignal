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


def extract_esma_date(text):
    """Parse the English date embedded in ESMA's description field."""
    m=re.search(r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})\b",text[:230],re.I)
    if not m: return None
    try:
        return datetime.strptime(" ".join(m.groups()),"%d %B %Y").date().isoformat()
    except ValueError:
        return None

def classify_signal(title, summary, authority):
    """First-pass headline triage; not legal or human editorial review."""
    t=title.lower()
    if re.search(r"commemorative coin|anniversary coin|collectors? coin|launches? .*coin\b",t):
        return "background","press/news"
    if re.search(r"unauthorised firm|unauthorized firm|\(clone\)|clone firm",t):
        return "monitor","firm warning"
    if re.search(r"\bspeech\b|opening remarks|\bremarks\b|keynote|fireside chat",t):
        return "background","speech"
    if re.search(r"hosts? .*conference|annual conference|helps? kids|celebrat|appointment of|commemorat",t):
        return "background","general news"
    if re.search(r"enforcement action|\bfines?\b|\bfined\b|\bpenalt|administrative sanction|breach of .*obligations",t):
        return "high","enforcement"
    if re.search(r"consultation|call for evidence|feedback on draft",t):
        return "high","consultation"
    if re.search(r"guidelines?|guidance|supervisory expectations|\bq&as?\b|technical standards?|regulatory technical",t):
        return "high","guidance"
    if re.search(r"enters? into force|takes? effect|new rules?|deadline|application date|implementation date",t):
        return "high","rule or deadline"
    if re.search(r"adopts? .*rules?|publishes? .*regulation|regulatory priorities|enforcement priorities",t):
        return "high","regulatory development"
    if re.search(r"strategy|annual report|research report|statement|opinion|decision",t):
        return "monitor","supervisory context"
    return "background","general news"

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
            if authority=="ESMA" and not date:
                date=extract_esma_date(summary)
        if not title or not date or not official(link) or not(first<=date<=last):
            continue
        terms=(title+" "+summary).lower()
        sectors=[sector for sector,keywords in KEYWORDS.items()
                 if any(re.search(r"(?<![a-z])"+re.escape(k)+r"(?![a-z])",terms) for k in keywords)]
        if authority=="EDPB" and "privacy" not in sectors: sectors.append("privacy")
        if authority=="ESMA" and "fin" not in sectors: sectors.append("fin")
        if not sectors: continue
        signal, event_type=classify_signal(title,summary,authority)
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
          "url":link,"sectors":sectors,"priority":"unassessed","sourceType":"rss","needsReview":True,
          "signalTier":signal,"eventType":event_type,
          "triageMethod":"headline rules; not human-reviewed"
        })
    return records


MAX_HISTORY_DAYS = 150
MAX_SNAPSHOT_ITEMS = 250

def load_previous_snapshot(path):
    """Return validated prior entries; never use the previous snapshot as a new observation."""
    if not path.exists():
        return {}
    try:
        doc=json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != "lexsignal-snapshot-v1" or not isinstance(doc.get("records"),list):
            return {}
        result={}
        for row in doc["records"]:
            if not isinstance(row,dict): continue
            rid=row.get("id")
            if not isinstance(rid,str) or not re.fullmatch(r"rss-[0-9a-f]{16}",rid):
                continue
            if row.get("authority") not in {name for name,_ in SOURCES}: continue
            if not isinstance(row.get("date"),str): continue
            if not official(row.get("url","")): continue
            result[rid]=row
        return result
    except (ValueError,TypeError,OSError):
        return {}

def merge_observations(current,previous,now,statuses):
    """Keep missing previously observed items for at most 150 days since publication."""
    moment=now.isoformat(timespec="seconds")
    start=(now-timedelta(days=MAX_HISTORY_DAYS)).date().isoformat()
    end=(now+timedelta(days=1)).date().isoformat()
    merged={}
    for rid,record in previous.items():
        if not(start<=record.get("date","")<=end):
            continue
        if not isinstance(record.get("title"),str):
            continue
        row=dict(record)
        row["collectionState"]="cached"
        row["firstSeenAt"]=record.get("firstSeenAt") or record.get("lastObservedAt") or record.get("date")
        row["lastObservedAt"]=record.get("lastObservedAt") or record.get("firstSeenAt")
        merged[rid]=row
    for rid,record in current.items():
        if not(start<=record.get("date","")<=end):
            continue
        row=dict(record)
        row["firstSeenAt"]=previous.get(rid,{}).get("firstSeenAt") or moment
        row["lastObservedAt"]=moment
        row["collectionState"]="observed"
        merged[rid]=row
    rows=sorted(merged.values(),key=lambda row:(row["date"],row["id"]),reverse=True)[:MAX_SNAPSHOT_ITEMS]
    for status in statuses:
        name=status["authority"]
        status["cachedRecordCount"]=sum(x["authority"]==name and x["collectionState"]=="cached" for x in rows)
        status["observedRecordCount"]=sum(x["authority"]==name and x["collectionState"]=="observed" for x in rows)
    return rows

def main():
    now=datetime.now(timezone.utc)
    dest=Path("data/regulatory_snapshot.json")
    previous=load_previous_snapshot(dest)
    current={}
    statuses=[]
    successes=0
    for name,url in SOURCES:
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"LexSignal/0.4 research-preview aggregator",
                "Accept":"application/rss+xml,application/atom+xml,text/xml,application/xml,*/*;q=0.5"})
            with urllib.request.urlopen(req,timeout=20) as reply:
                if reply.status!=200: raise ValueError("HTTP "+str(reply.status))
                xml=reply.read(2_000_001)
            if len(xml)>2_000_000: raise ValueError("Feed >2 MB")
            recs=parse(xml,name,now)
            successes+=1
            for item in recs: current[item["id"]]=item
            statuses.append({"authority":name,"url":url,"status":"ok","matched":len(recs)})
            print(name,"OK",len(recs))
        except Exception as exc:
            statuses.append({"authority":name,"url":url,"status":"error",
                             "matched":0,"message":type(exc).__name__+": "+str(exc)[:180]})
            print(name,"ERROR",type(exc).__name__,str(exc)[:180],file=sys.stderr)
    if successes==0:
        print("No feeds succeeded; retaining existing snapshot.",file=sys.stderr)
        return 1
    rows=merge_observations(current,previous,now,statuses)
    doc={"schema":"lexsignal-snapshot-v1","generatedAt":now.isoformat(timespec="seconds"),
         "disclaimer":("Automatically classified RSS extracts, not human-reviewed. "
                       "Cached records may no longer be in the latest RSS feed. "
                       "See collectionState and lastObservedAt."),
         "sources":statuses,"records":rows}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Snapshot:",len(rows),"records; cached:",
          sum(r["collectionState"]=="cached" for r in rows),
          "source failures:",len(SOURCES)-successes)
    return 0

if __name__=="__main__": sys.exit(main())
