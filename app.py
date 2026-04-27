from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
import io
import csv

app = FastAPI()

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

BLOCKED_PROVIDERS = [
    "gmail.com","yahoo.com","hotmail.com","outlook.com"
]

class DomainInput(BaseModel):
    domains: list[str]


def is_valid(email):
    email = email.lower()

    if any(p in email for p in BLOCKED_PROVIDERS):
        return False

    if any(ext in email for ext in [".png",".jpg",".jpeg",".gif",".svg"]):
        return False

    return True


def extract_emails_from_url(url):
    emails = set()
    try:
        res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return emails

        soup = BeautifulSoup(res.text, "html.parser")

        found = EMAIL_REGEX.findall(res.text)
        for e in found:
            if is_valid(e):
                emails.add(e)

        links = [a.get("href") for a in soup.find_all("a", href=True)]

        for link in links[:5]:
            full_url = urljoin(url, link)
            try:
                r = requests.get(full_url, timeout=5)
                found2 = EMAIL_REGEX.findall(r.text)
                for e in found2:
                    if is_valid(e):
                        emails.add(e)
            except:
                pass

    except:
        pass

    return emails


def process_domain(domain):
    urls = [
        f"https://{domain}",
        f"https://{domain}/contact",
        f"https://{domain}/about"
    ]

    emails = set()
    for url in urls:
        emails.update(extract_emails_from_url(url))

    return emails


def run_extraction(domains):
    all_emails = set()

    with ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(process_domain, domains)

    for r in results:
        all_emails.update(r)

    return list(all_emails)


# JSON endpoint
@app.post("/extract")
def extract(data: DomainInput):
    emails = run_extraction(data.domains)
    return {"emails": emails}


# ✅ CSV endpoint
@app.post("/extract-csv")
def extract_csv(data: DomainInput):
    emails = run_extraction(data.domains)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["email"])  # header
    for e in emails:
        writer.writerow([e])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=emails.csv"
        }
    )