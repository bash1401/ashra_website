#!/usr/bin/env python3
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup


WIKI_UNIVERSITIES_LIST = "https://en.wikipedia.org/wiki/List_of_universities_in_India"
WIKI_GLOBAL_INDEX = "https://en.wikipedia.org/wiki/Lists_of_universities_and_colleges_by_country"


@dataclass
class University:
    name: str
    url: Optional[str]
    kind: Optional[str]


async def fetch(session: aiohttp.ClientSession, url: str, *, timeout: int = 20) -> Optional[str]:
    try:
        async with session.get(url, timeout=timeout, headers={"User-Agent": "BashTech-GPACalc-Crawler/1.0"}) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
    except Exception:
        return None


def extract_universities_from_wikipedia(html: str) -> List[University]:
    soup = BeautifulSoup(html, "html.parser")
    universities: List[University] = []
    # Wikipedia page has multiple lists/tables; we collect anchors that look like university pages
    for li in soup.select("li a"):  # broad
        name = (li.get_text() or "").strip()
        href = li.get("href")
        if not name or not href:
            continue
        # Heuristics: skip in-page anchors and non-article links
        if href.startswith("#") or not href.startswith("/wiki/"):
            continue
        # Filter obvious non-university items
        if any(token in name.lower() for token in ["list of", "states and union territories", "ugc", "nai", "ranking", "accreditation"]):
            continue
        # Likely university if name contains: university, institute, college, academy, national law, iit, nit, iiit, iisc
        lowered = name.lower()
        is_university_like = any(
            kw in lowered for kw in [
                "university", "institute", "college", "academy", "iit", "nit", "iiit", "iisc", "law university", "state university"
            ]
        )
        if not is_university_like:
            continue
        # Compose Wikipedia URL as homepage candidate fallback
        universities.append(University(name=name, url="https://en.wikipedia.org" + href, kind=None))
    # De-duplicate by name
    seen = set()
    unique: List[University] = []
    for u in universities:
        key = u.name.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(u)
    return unique


def guess_scale_from_tokens(tokens: List[str]) -> Optional[float]:
    joined = " ".join(tokens).lower()
    # Common Indian scales
    if re.search(r"\b(outstanding|o\s*grade)\b", joined) and "10" in joined:
        return 10.0
    if re.search(r"\bsgpa|cgpa\b", joined) and re.search(r"10\s*point|10-point|\b/10\b", joined):
        return 10.0
    if re.search(r"7\s*point|7-point|\b/7\b", joined):
        return 7.0
    if re.search(r"\b/4\b|4\.0\s*scale", joined):
        return 4.0
    return None


def try_parse_grading_table(soup: BeautifulSoup) -> Optional[Tuple[float, List[Dict[str, Any]]]]:
    # Look for tables that have headers like Grade/Letter/Points/Credit/Percentage
    candidate_tables = []
    for table in soup.select("table"):
        header_text = " ".join(th.get_text(" ", strip=True) for th in table.select("th"))
        if not header_text:
            continue
        if any(k in header_text.lower() for k in ["grade", "letter", "points", "credit", "percentage", "marks"]):
            candidate_tables.append(table)
    for table in candidate_tables:
        rows = []
        for tr in table.select("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.select("td")]
            if len(cells) < 2:
                continue
            rows.append(cells)
        if len(rows) < 2:
            continue
        # Heuristic: find columns for grade, points, percentage
        # Assume first column has grade label, any float-like cell as points
        grades: List[Dict[str, Any]] = []
        scale_guess = None
        for r in rows:
            grade_label = r[0]
            points = None
            percentage = None
            # Find numeric token as points
            for cell in r[1:]:
                m = re.search(r"\d+(?:\.\d+)?", cell)
                if m:
                    try:
                        val = float(m.group(0))
                    except Exception:
                        continue
                    points = val
                    break
            # Percentage range detection
            for cell in r[1:]:
                if re.search(r"\b\d{1,3}\s*-\s*\d{1,3}\b", cell):
                    percentage = re.sub(r"\s+", "", cell)
                    break
            if not grade_label or points is None:
                continue
            grades.append({"grade": grade_label, "points": points, **({"percentage": percentage} if percentage else {})})
        if not grades:
            continue
        # Determine scale as max points or guess
        max_points = max((g.get("points") for g in grades if isinstance(g.get("points"), (int, float))), default=None)
        tokens = [t.get_text(" ", strip=True) for t in table.find_all(True)]
        scale_guess = guess_scale_from_tokens(tokens) or (float(max_points) if isinstance(max_points, (int, float)) else None)
        if scale_guess is None:
            continue
        # If the majority of points exceed 10, but a 100-mark system is implied, map to 100
        if any(g.get("points", 0) > 10 for g in grades) and scale_guess <= 10:
            # Likely not a point scale we want
            continue
        return scale_guess, grades
    return None


async def find_and_parse_grading(session: aiohttp.ClientSession, homepage_url: str) -> Optional[Tuple[float, List[Dict[str, Any]]]]:
    # Explore homepage and likely subsections
    to_visit = [homepage_url]
    visited = set()
    # Keywords often used for grading/academics
    key_patterns = ["academic", "regulation", "ordinance", "examination", "grading", "evaluation", "credit", "curriculum"]
    try:
        base = re.match(r"https?://[^/]+", homepage_url)
        base_url = base.group(0) if base else homepage_url
    except Exception:
        base_url = homepage_url
    max_pages = 5
    results: Optional[Tuple[float, List[Dict[str, Any]]]] = None
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        html = await fetch(session, url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        # Try parse on this page
        parsed = try_parse_grading_table(soup)
        if parsed:
            results = parsed
            break
        # Queue likely links
        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href:
                continue
            if href.startswith("/"):
                next_url = base_url + href
            elif href.startswith("http://") or href.startswith("https://"):
                next_url = href
            else:
                continue
            text = (a.get_text() or "").lower()
            if any(k in text or k in href.lower() for k in key_patterns):
                to_visit.append(next_url)
    return results


def normalize_system(name: str, country: str, region: str, scale: float, grades: List[Dict[str, Any]]) -> Dict[str, Any]:
    system_id = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return {
        "id": system_id,
        "name": name,
        "country": country,
        "region": region,
        "description": f"{name} grading system",
        "scale": scale,
        "grades": grades,
    }


async def crawl_indian_universities() -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        wiki_html = await fetch(session, WIKI_UNIVERSITIES_LIST)
        if not wiki_html:
            return []
        universities = extract_universities_from_wikipedia(wiki_html)
        systems: List[Dict[str, Any]] = []
        # Limit initial run size to be respectful; can be increased
        concurrency = 10
        sem = asyncio.Semaphore(concurrency)

        async def process_uni(u: University):
            homepage = u.url
            if not homepage:
                return
            async with sem:
                parsed = await find_and_parse_grading(session, homepage)
            if parsed:
                scale, grades = parsed
                systems.append(normalize_system(name=u.name, country="India", region="South Asia", scale=scale, grades=grades))

        tasks = [asyncio.create_task(process_uni(u)) for u in universities]
        await asyncio.gather(*tasks)
        return systems


async def crawl_world_universities() -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        index_html = await fetch(session, WIKI_GLOBAL_INDEX)
        if not index_html:
            return []
        soup = BeautifulSoup(index_html, "html.parser")
        country_links: List[Tuple[str, str]] = []  # (url, country)
        for a in soup.select("a[href]"):
            text = (a.get_text() or "").strip()
            href = a.get("href")
            if not text or not href:
                continue
            if not href.startswith("/wiki/"):
                continue
            # Heuristic: link text like "List of universities in <Country>"
            m1 = re.match(r"List of universities.* in (.+)", text, flags=re.I)
            m2 = re.match(r"List of colleges.* in (.+)", text, flags=re.I)
            m = m1 or m2
            if m:
                country_name = m.group(1).strip()
                country_links.append(("https://en.wikipedia.org" + href, country_name))
        # Deduplicate
        seen = set()
        deduped: List[Tuple[str, str]] = []
        for url, country in country_links:
            key = (url, country.lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append((url, country))
        country_links = deduped
        systems: List[Dict[str, Any]] = []

        sem = asyncio.Semaphore(8)

        async def process_country(list_url: str, country: str):
            html = await fetch(session, list_url)
            if not html:
                return
            unis = extract_universities_from_wikipedia(html)
            for u in unis:
                async with sem:
                    parsed = await find_and_parse_grading(session, u.url or "")
                if parsed:
                    scale, grades = parsed
                    region = "Unknown"
                    systems.append({
                        "id": re.sub(r"[^a-z0-9]+", "_", f"{country}_{u.name}".lower()).strip("_"),
                        "name": f"{u.name} ({country})",
                        "country": country,
                        "region": region,
                        "description": f"{u.name} grading system",
                        "scale": scale,
                        "grades": grades
                    })

        tasks = [asyncio.create_task(process_country(url, country)) for (url, country) in country_links]
        await asyncio.gather(*tasks)
        return systems


def is_valid_indian_system(system: Dict[str, Any]) -> bool:
    # Only allow plausible Indian scales and sensible grade rows
    allowed_scales = {10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.33, 4.0, 100.0}
    scale = system.get("scale")
    if not isinstance(scale, (int, float)):
        return False
    if float(scale) not in allowed_scales:
        return False
    grades = system.get("grades")
    if not isinstance(grades, list) or len(grades) < 3:
        return False
    def looks_like_grade_label(label: str) -> bool:
        label = (label or "").strip()
        if not label or len(label) > 20:
            return False
        # Accept letters like O, S, A+, A, B-, etc., or small numeric tokens like 10, 9, 8, 30L
        if re.fullmatch(r"[OSAUBCDFEP]{1,2}[+-]?|[A-D][+-]?|HD|D|C|P|F|First|Pass|Fail", label):
            return True
        if re.fullmatch(r"\d{1,3}(?:L)?", label):
            return True
        if label in {"O", "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "E", "P", "F", "HD"}:
            return True
        return False
    seen_labels = set()
    for row in grades:
        if not isinstance(row, dict):
            return False
        grade_label = row.get("grade")
        points = row.get("points")
        if not isinstance(points, (int, float)):
            return False
        if points < 0 or points > float(scale) + 1e-6:
            return False
        if not isinstance(grade_label, str) or not looks_like_grade_label(grade_label):
            return False
        if grade_label in seen_labels:
            return False
        seen_labels.add(grade_label)
    return True


def merge_into_existing(existing: Dict[str, Any], new_systems: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Start with existing but drop obviously invalid Indian entries
    cleaned_existing: List[Dict[str, Any]] = []
    for s in existing.get("systems", []):
        if s.get("country") == "India":
            if not is_valid_indian_system(s):
                continue
        cleaned_existing.append(s)
    by_id = {s.get("id"): s for s in cleaned_existing}
    for s in new_systems:
        sid = s.get("id")
        if not sid:
            continue
        # Upsert by id, only if valid
        if s.get("country") == "India" and not is_valid_indian_system(s):
            continue
        by_id[sid] = s
    merged = dict(existing)
    merged["systems"] = list(by_id.values())
    # bump version minor and update lastUpdated
    version = existing.get("version", "1.0.0")
    parts = version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        merged["version"] = ".".join(parts)
    except Exception:
        merged["version"] = version
    from datetime import datetime
    merged["lastUpdated"] = datetime.utcnow().date().isoformat()
    return merged


def country_baselines() -> List[Dict[str, Any]]:
    # Standard national scales (conservative selection) — schema-compatible
    baselines: List[Dict[str, Any]] = [
        {
            "id": "china_100",
            "name": "China 100-Point Scale",
            "country": "China",
            "region": "East Asia",
            "description": "Chinese 0–100 scale",
            "scale": 100.0,
            "grades": [
                {"grade": "Excellent", "points": 95.0, "percentage": "95-100"},
                {"grade": "Very Good", "points": 85.0, "percentage": "85-94"},
                {"grade": "Good", "points": 75.0, "percentage": "75-84"},
                {"grade": "Satisfactory", "points": 65.0, "percentage": "65-74"},
                {"grade": "Pass", "points": 60.0, "percentage": "60-64"},
                {"grade": "Fail", "points": 0.0, "percentage": "0-59"}
            ],
        },
        {
            "id": "russia_5",
            "name": "Russia 5-Point Scale",
            "country": "Russia",
            "region": "Europe",
            "description": "Russian 5-point scale (5=Excellent, 2=Unsatisfactory)",
            "scale": 5.0,
            "grades": [
                {"grade": "5", "points": 5.0, "percentage": "85-100", "description": "Excellent"},
                {"grade": "4", "points": 4.0, "percentage": "70-84", "description": "Good"},
                {"grade": "3", "points": 3.0, "percentage": "60-69", "description": "Satisfactory"},
                {"grade": "2", "points": 0.0, "percentage": "0-59", "description": "Unsatisfactory"}
            ],
        },
        {
            "id": "portugal_20",
            "name": "Portugal 20-Point Scale",
            "country": "Portugal",
            "region": "Europe",
            "description": "Portuguese 0–20 scale",
            "scale": 20.0,
            "grades": [
                {"grade": "20", "points": 20.0, "percentage": "95-100"},
                {"grade": "18-19", "points": 19.0, "percentage": "90-94"},
                {"grade": "16-17", "points": 17.0, "percentage": "80-89"},
                {"grade": "14-15", "points": 15.0, "percentage": "70-79"},
                {"grade": "10-13", "points": 12.0, "percentage": "50-69"},
                {"grade": "0-9", "points": 0.0, "percentage": "0-49"}
            ],
        },
        {
            "id": "austria_5",
            "name": "Austria 5-Point Scale",
            "country": "Austria",
            "region": "Europe",
            "description": "Austrian 1–5 scale (1=Sehr gut, 5=Nicht genügend)",
            "scale": 5.0,
            "grades": [
                {"grade": "1", "points": 1.0, "percentage": "90-100", "description": "Sehr gut"},
                {"grade": "2", "points": 2.0, "percentage": "80-89", "description": "Gut"},
                {"grade": "3", "points": 3.0, "percentage": "65-79", "description": "Befriedigend"},
                {"grade": "4", "points": 4.0, "percentage": "50-64", "description": "Genügend"},
                {"grade": "5", "points": 5.0, "percentage": "0-49", "description": "Nicht genügend"}
            ],
        },
        {
            "id": "czech_1_4",
            "name": "Czech Republic 1–4 Scale",
            "country": "Czech Republic",
            "region": "Europe",
            "description": "Czech 1–4 scale (1=best, 4=fail)",
            "scale": 4.0,
            "grades": [
                {"grade": "1", "points": 1.0, "percentage": "90-100", "description": "Výborně"},
                {"grade": "2", "points": 2.0, "percentage": "75-89", "description": "Velmi dobře"},
                {"grade": "3", "points": 3.0, "percentage": "60-74", "description": "Dobře"},
                {"grade": "4", "points": 4.0, "percentage": "0-59", "description": "Nedostatečně"}
            ],
        },
        {
            "id": "poland_2_5",
            "name": "Poland 2–5 Scale",
            "country": "Poland",
            "region": "Europe",
            "description": "Polish 2–5 scale (5=very good, 2=fail)",
            "scale": 5.0,
            "grades": [
                {"grade": "5", "points": 5.0, "percentage": "90-100", "description": "Bardzo dobry"},
                {"grade": "4", "points": 4.0, "percentage": "75-89", "description": "Dobry"},
                {"grade": "3", "points": 3.0, "percentage": "60-74", "description": "Dostateczny"},
                {"grade": "2", "points": 0.0, "percentage": "0-59", "description": "Niedostateczny"}
            ],
        },
        {
            "id": "hungary_5",
            "name": "Hungary 5-Point Scale",
            "country": "Hungary",
            "region": "Europe",
            "description": "Hungarian 1–5 scale (5=Jeles, 1=Elégtelen)",
            "scale": 5.0,
            "grades": [
                {"grade": "5", "points": 5.0, "percentage": "90-100", "description": "Jeles"},
                {"grade": "4", "points": 4.0, "percentage": "80-89", "description": "Jó"},
                {"grade": "3", "points": 3.0, "percentage": "65-79", "description": "Közepes"},
                {"grade": "2", "points": 2.0, "percentage": "50-64", "description": "Elégséges"},
                {"grade": "1", "points": 0.0, "percentage": "0-49", "description": "Elégtelen"}
            ],
        },
        {
            "id": "romania_10",
            "name": "Romania 10-Point Scale",
            "country": "Romania",
            "region": "Europe",
            "description": "Romanian 1–10 scale",
            "scale": 10.0,
            "grades": [
                {"grade": "10", "points": 10.0, "percentage": "95-100"},
                {"grade": "9", "points": 9.0, "percentage": "85-94"},
                {"grade": "8", "points": 8.0, "percentage": "75-84"},
                {"grade": "7", "points": 7.0, "percentage": "65-74"},
                {"grade": "6", "points": 6.0, "percentage": "55-64"},
                {"grade": "5", "points": 5.0, "percentage": "50-54"},
                {"grade": "0-4", "points": 0.0, "percentage": "0-49"}
            ],
        },
        {
            "id": "greece_10",
            "name": "Greece 10-Point Scale",
            "country": "Greece",
            "region": "Europe",
            "description": "Greek 0–10 scale",
            "scale": 10.0,
            "grades": [
                {"grade": "9-10", "points": 9.5, "percentage": "90-100", "description": "Άριστα"},
                {"grade": "7-8.9", "points": 8.0, "percentage": "70-89", "description": "Λίαν Καλώς"},
                {"grade": "5-6.9", "points": 6.0, "percentage": "50-69", "description": "Καλώς"},
                {"grade": "0-4.9", "points": 0.0, "percentage": "0-49", "description": "Ανεπιτυχώς"}
            ],
        },
        {
            "id": "turkey_100",
            "name": "Turkey 100-Point Scale",
            "country": "Turkey",
            "region": "Europe",
            "description": "Turkish 0–100 scale",
            "scale": 100.0,
            "grades": [
                {"grade": "90-100", "points": 95.0, "percentage": "90-100", "description": "AA"},
                {"grade": "80-89", "points": 85.0, "percentage": "80-89", "description": "BA/BB"},
                {"grade": "70-79", "points": 75.0, "percentage": "70-79", "description": "CB/CC"},
                {"grade": "60-69", "points": 65.0, "percentage": "60-69", "description": "DC/DD"},
                {"grade": "50-59", "points": 55.0, "percentage": "50-59", "description": "FD"},
                {"grade": "0-49", "points": 0.0, "percentage": "0-49", "description": "FF"}
            ],
        },
        {
            "id": "argentina_10",
            "name": "Argentina 10-Point Scale",
            "country": "Argentina",
            "region": "South America",
            "description": "Argentine 0–10 scale",
            "scale": 10.0,
            "grades": [
                {"grade": "10", "points": 10.0, "percentage": "95-100"},
                {"grade": "9", "points": 9.0, "percentage": "90-94"},
                {"grade": "8", "points": 8.0, "percentage": "80-89"},
                {"grade": "7", "points": 7.0, "percentage": "70-79"},
                {"grade": "6", "points": 6.0, "percentage": "60-69"},
                {"grade": "0-5", "points": 0.0, "percentage": "0-59"}
            ],
        },
        {
            "id": "chile_7",
            "name": "Chile 7-Point Scale",
            "country": "Chile",
            "region": "South America",
            "description": "Chilean 1.0–7.0 scale",
            "scale": 7.0,
            "grades": [
                {"grade": "7.0", "points": 7.0, "percentage": "95-100", "description": "Sobresaliente"},
                {"grade": "6.0", "points": 6.0, "percentage": "85-94", "description": "Muy bueno"},
                {"grade": "5.0", "points": 5.0, "percentage": "75-84", "description": "Bueno"},
                {"grade": "4.0", "points": 4.0, "percentage": "60-74", "description": "Suficiente"},
                {"grade": "1.0-3.9", "points": 0.0, "percentage": "0-59", "description": "Insuficiente"}
            ],
        },
        {
            "id": "colombia_5",
            "name": "Colombia 5-Point Scale",
            "country": "Colombia",
            "region": "South America",
            "description": "Colombian 0–5 scale",
            "scale": 5.0,
            "grades": [
                {"grade": "5.0", "points": 5.0, "percentage": "90-100"},
                {"grade": "4.0", "points": 4.0, "percentage": "80-89"},
                {"grade": "3.0", "points": 3.0, "percentage": "70-79"},
                {"grade": "2.0", "points": 2.0, "percentage": "60-69"},
                {"grade": "0-1.9", "points": 0.0, "percentage": "0-59"}
            ],
        },
        {
            "id": "peru_20",
            "name": "Peru 20-Point Scale",
            "country": "Peru",
            "region": "South America",
            "description": "Peruvian 0–20 scale",
            "scale": 20.0,
            "grades": [
                {"grade": "18-20", "points": 19.0, "percentage": "90-100"},
                {"grade": "14-17", "points": 15.0, "percentage": "70-89"},
                {"grade": "11-13", "points": 12.0, "percentage": "55-69"},
                {"grade": "0-10", "points": 0.0, "percentage": "0-54"}
            ],
        },
        {
            "id": "philippines_5",
            "name": "Philippines 1.0–5.0 Scale",
            "country": "Philippines",
            "region": "Southeast Asia",
            "description": "Philippine 1.0 (best) to 5.0 (fail)",
            "scale": 5.0,
            "grades": [
                {"grade": "1.0", "points": 1.0, "percentage": "96-100", "description": "Excellent"},
                {"grade": "1.5", "points": 1.5, "percentage": "90-95"},
                {"grade": "2.0", "points": 2.0, "percentage": "84-89"},
                {"grade": "2.5", "points": 2.5, "percentage": "78-83"},
                {"grade": "3.0", "points": 3.0, "percentage": "75-77", "description": "Pass"},
                {"grade": "5.0", "points": 5.0, "percentage": "0-74", "description": "Fail"}
            ],
        },
        {
            "id": "malaysia_4_0",
            "name": "Malaysia 4.0 Scale",
            "country": "Malaysia",
            "region": "Southeast Asia",
            "description": "Malaysian 4.0 GPA scale",
            "scale": 4.0,
            "grades": [
                {"grade": "A", "points": 4.0, "percentage": "80-100"},
                {"grade": "A-", "points": 3.7, "percentage": "75-79"},
                {"grade": "B+", "points": 3.3, "percentage": "70-74"},
                {"grade": "B", "points": 3.0, "percentage": "65-69"},
                {"grade": "B-", "points": 2.7, "percentage": "60-64"},
                {"grade": "C+", "points": 2.3, "percentage": "55-59"},
                {"grade": "C", "points": 2.0, "percentage": "50-54"},
                {"grade": "F", "points": 0.0, "percentage": "0-49"}
            ],
        },
        {
            "id": "indonesia_4_0",
            "name": "Indonesia 4.0 Scale",
            "country": "Indonesia",
            "region": "Southeast Asia",
            "description": "Indonesian 4.0 GPA scale",
            "scale": 4.0,
            "grades": [
                {"grade": "A", "points": 4.0, "percentage": "85-100"},
                {"grade": "A-", "points": 3.7, "percentage": "80-84"},
                {"grade": "B+", "points": 3.3, "percentage": "75-79"},
                {"grade": "B", "points": 3.0, "percentage": "70-74"},
                {"grade": "C+", "points": 2.3, "percentage": "65-69"},
                {"grade": "C", "points": 2.0, "percentage": "60-64"},
                {"grade": "D", "points": 1.0, "percentage": "50-59"},
                {"grade": "E", "points": 0.0, "percentage": "0-49"}
            ],
        },
        {
            "id": "singapore_5_0",
            "name": "Singapore 5.0 Scale",
            "country": "Singapore",
            "region": "Southeast Asia",
            "description": "Singaporean 5.0 GPA scale variant",
            "scale": 5.0,
            "grades": [
                {"grade": "A+", "points": 5.0},
                {"grade": "A", "points": 5.0},
                {"grade": "A-", "points": 4.5},
                {"grade": "B+", "points": 4.0},
                {"grade": "B", "points": 3.5},
                {"grade": "B-", "points": 3.0},
                {"grade": "C+", "points": 2.5},
                {"grade": "C", "points": 2.0},
                {"grade": "D", "points": 1.0},
                {"grade": "F", "points": 0.0}
            ],
        },
        {
            "id": "saudi_arabia_5_0",
            "name": "Saudi Arabia 5.0 Scale",
            "country": "Saudi Arabia",
            "region": "Middle East",
            "description": "Saudi 5.0 GPA scale",
            "scale": 5.0,
            "grades": [
                {"grade": "A+", "points": 5.0},
                {"grade": "A", "points": 4.5},
                {"grade": "B+", "points": 4.0},
                {"grade": "B", "points": 3.5},
                {"grade": "C+", "points": 3.0},
                {"grade": "C", "points": 2.5},
                {"grade": "D+", "points": 2.0},
                {"grade": "D", "points": 1.0},
                {"grade": "F", "points": 0.0}
            ],
        },
        {
            "id": "uae_4_0",
            "name": "UAE 4.0 Scale",
            "country": "United Arab Emirates",
            "region": "Middle East",
            "description": "UAE 4.0 GPA scale",
            "scale": 4.0,
            "grades": [
                {"grade": "A", "points": 4.0},
                {"grade": "A-", "points": 3.7},
                {"grade": "B+", "points": 3.3},
                {"grade": "B", "points": 3.0},
                {"grade": "C+", "points": 2.3},
                {"grade": "C", "points": 2.0},
                {"grade": "D", "points": 1.0},
                {"grade": "F", "points": 0.0}
            ],
        },
        {
            "id": "iran_20",
            "name": "Iran 20-Point Scale",
            "country": "Iran",
            "region": "Middle East",
            "description": "Iranian 0–20 scale",
            "scale": 20.0,
            "grades": [
                {"grade": "18-20", "points": 19.0, "percentage": "90-100"},
                {"grade": "15-17", "points": 16.0, "percentage": "75-89"},
                {"grade": "10-14", "points": 12.0, "percentage": "50-74"},
                {"grade": "0-9", "points": 0.0, "percentage": "0-49"}
            ],
        },
        {
            "id": "pakistan_4_0",
            "name": "Pakistan 4.0 Scale",
            "country": "Pakistan",
            "region": "South Asia",
            "description": "Pakistani 4.0 GPA scale",
            "scale": 4.0,
            "grades": [
                {"grade": "A", "points": 4.0},
                {"grade": "B", "points": 3.0},
                {"grade": "C", "points": 2.0},
                {"grade": "D", "points": 1.0},
                {"grade": "F", "points": 0.0}
            ],
        },
        {
            "id": "nigeria_5_0",
            "name": "Nigeria 5.0 Scale",
            "country": "Nigeria",
            "region": "Africa",
            "description": "Nigerian 5.0 GPA scale",
            "scale": 5.0,
            "grades": [
                {"grade": "A", "points": 5.0},
                {"grade": "B", "points": 4.0},
                {"grade": "C", "points": 3.0},
                {"grade": "D", "points": 2.0},
                {"grade": "E", "points": 1.0},
                {"grade": "F", "points": 0.0}
            ],
        },
        {
            "id": "kenya_100",
            "name": "Kenya 100-Point Scale",
            "country": "Kenya",
            "region": "Africa",
            "description": "Kenyan 0–100 with letter categories",
            "scale": 100.0,
            "grades": [
                {"grade": "A", "points": 90.0, "percentage": "80-100"},
                {"grade": "B", "points": 70.0, "percentage": "65-79"},
                {"grade": "C", "points": 55.0, "percentage": "50-64"},
                {"grade": "D", "points": 40.0, "percentage": "40-49"},
                {"grade": "E", "points": 0.0, "percentage": "0-39"}
            ],
        }
    ]
    return baselines


def main() -> int:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(repo_root, "gpacalculator", "grading-systems.json")
    if not os.path.exists(json_path):
        print(f"grading-systems.json not found at {json_path}", file=sys.stderr)
        return 1
    try:
        existing = json.load(open(json_path, "r", encoding="utf-8"))
    except Exception as e:
        print(f"Failed to read JSON: {e}", file=sys.stderr)
        return 1
    world = "--world" in sys.argv
    countries_mode = "--countries" in sys.argv
    if world:
        new_systems = asyncio.run(crawl_world_universities())
    elif countries_mode:
        new_systems = country_baselines()
    else:
        new_systems = asyncio.run(crawl_indian_universities())
    if not new_systems:
        print("No systems discovered; nothing to update.")
        return 0
    merged = merge_into_existing(existing, new_systems)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Merged {len(new_systems)} systems into grading-systems.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


