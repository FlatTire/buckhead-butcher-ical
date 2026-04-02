#!/usr/bin/env python3
"""
Scrape Buckhead Butcher Shop classes/events and generate iCal file.
"""

import re
from datetime import datetime, timedelta

import pytz
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

BASE_URL = "https://buckheadbutchershop.com"
CLASSES_PAGE = f"{BASE_URL}/classes-events/"
OUTPUT_FILE = "buckhead_butcher_classes.ics"

# Eastern timezone
EASTERN = pytz.timezone("US/Eastern")


def parse_date_time(date_str, time_str, reference_date=None):
    """
    Parse date and time strings into a datetime object.

    Args:
        date_str: e.g., "Saturday, November 28th"
        time_str: e.g., "6:30 pm"
        reference_date: datetime to determine the year

    Returns:
        datetime object in Eastern timezone
    """
    if reference_date is None:
        reference_date = datetime.now(tz=EASTERN)

    # Parse time
    time_match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str.lower())
    if not time_match:
        raise ValueError(f"Could not parse time: {time_str}")

    hour = int(time_match.group(1))
    minute = int(time_match.group(2))
    am_pm = time_match.group(3)

    if am_pm == "pm" and hour != 12:
        hour += 12
    elif am_pm == "am" and hour == 12:
        hour = 0

    # Parse date (e.g., "Saturday, November 28th")
    date_match = re.search(r"([A-Za-z]+),?\s+([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?", date_str)
    if not date_match:
        raise ValueError(f"Could not parse date: {date_str}")

    month_name = date_match.group(2)
    day = int(date_match.group(3))

    # Get month number
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    month = months.get(month_name.lower())
    if not month:
        raise ValueError(f"Could not parse month: {month_name}")

    # Determine year - use current year or next year if date has passed
    year = reference_date.year
    try:
        dt = datetime(year, month, day, hour, minute, 0, tzinfo=EASTERN)
        # If the date is in the past, try next year
        if dt < reference_date:
            dt = datetime(year + 1, month, day, hour, minute, 0, tzinfo=EASTERN)
    except ValueError:
        # Invalid date, try next year
        dt = datetime(year + 1, month, day, hour, minute, 0, tzinfo=EASTERN)

    return dt


def fetch_page(url):
    """Fetch and parse a webpage."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def scrape_event_links():
    """Scrape the main classes/events page and return list of event URLs."""
    print(f"Fetching {CLASSES_PAGE}...")
    soup = fetch_page(CLASSES_PAGE)

    events = []

    # Look for event links - they're typically in anchor tags
    for link in soup.find_all("a", href=True):
        href = link.get("href", "").strip()
        text = link.get_text(strip=True)

        # Filter for event links:
        # - Must start with BASE_URL
        # - Must contain "class" in href (not just text)
        # - Must not be the main classes-events page itself
        # - Should have meaningful text
        if (
            href.startswith(BASE_URL)
            and "classes-events" not in href
            and "class" in href.lower()
            and text
            and len(text) > 5
        ):
            if href not in [e["url"] for e in events]:
                events.append({"title": text, "url": href})

    return events


def scrape_event_details(event_url):
    """Scrape details from an individual event page."""
    print(f"  Fetching {event_url}...")
    soup = fetch_page(event_url)

    # Extract full text
    body_text = soup.get_text()

    # Look for date pattern in URL first (more reliable)
    # Patterns: "steak-class-saturday-november-28th-6-30-pm"
    url_date_pattern = r"([a-z]+)-([a-z]+)-(\d{1,2})(?:st|nd|rd|th)?-(\d{1,2})-(\d{2})-([ap]m)"
    url_match = re.search(url_date_pattern, event_url)

    date_match = None
    time_match = None

    if url_match:
        # Extract from URL
        day_name = url_match.group(1)
        month_name = url_match.group(2)
        day = url_match.group(3)
        hour = url_match.group(4)
        minute = url_match.group(5)
        am_pm = url_match.group(6)
        date_str = f"{day_name.capitalize()}, {month_name.capitalize()} {day}"
        time_str = f"{hour}:{minute} {am_pm}"
    else:
        # Fallback to body text parsing
        # Look for date pattern: e.g., "Saturday, November 28th"
        # Only look in first 500 chars to avoid "Christmas" in footer or sidebar
        search_text = body_text[:1000]
        date_pattern = r"([A-Za-z]+),?\s+([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?"
        date_match = re.search(date_pattern, search_text)

        # Look for time pattern: e.g., "6:30 pm"
        time_pattern = r"(\d{1,2}):(\d{2})\s*(am|pm)"
        time_match = re.search(time_pattern, search_text)

        if date_match and time_match:
            date_str = f"{date_match.group(1)}, {date_match.group(2)} {date_match.group(3)}"
            time_str = time_match.group(0)
        else:
            date_str = None
            time_str = None

    # Look for location
    location = "Buckhead Butcher Shop, 3198 Cains Hill Place NW, Atlanta GA 30305"
    location_match = re.search(r"([\d\s,A-Za-z]+(?:Atlanta|GA|Georgia)[\d\s,A-Za-z]*)", body_text)
    if location_match:
        location = location_match.group(0).strip()

    # Extract description (first few paragraphs)
    description = ""
    paragraphs = soup.find_all("p")
    if paragraphs:
        # Get text from paragraphs, filtering out navigation/footer elements
        desc_parts = []
        for p in paragraphs[:5]:  # Take first 5 paragraphs
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Skip very short paragraphs
                desc_parts.append(text)
        description = "\n\n".join(desc_parts)

    if not description:
        description = "Cooking class at Buckhead Butcher Shop"

    # Parse datetime
    if date_str and time_str:
        try:
            dt = parse_date_time(date_str, time_str)
        except ValueError as e:
            print(f"    Warning: Could not parse date/time ({date_str}, {time_str}): {e}")
            dt = datetime.now(tz=EASTERN)
    else:
        # Fallback if parsing fails
        print(f"    Warning: Could not parse date/time from {event_url}")
        dt = datetime.now(tz=EASTERN)

    return {
        "title": soup.title.string if soup.title else "Buckhead Butcher Class",
        "datetime": dt,
        "location": location,
        "description": description,
        "url": event_url,
    }


def create_ical(events):
    """Create an iCalendar object from event data."""
    cal = Calendar()
    cal.add("prodid", "-//Buckhead Butcher Shop//Classes & Events//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Buckhead Butcher Shop Classes & Events")
    cal.add("x-wr-timezone", "US/Eastern")

    for event_data in events:
        event = Event()
        event.add("summary", event_data["title"])
        event.add("dtstart", event_data["datetime"])
        # Assume 2-hour class duration
        event.add("dtend", event_data["datetime"] + timedelta(hours=2))
        event.add("location", event_data["location"])
        event.add("description", event_data["description"])
        event.add("url", event_data["url"])
        event.add("uid", f"{event_data['url']}@buckheadbutchershop.com")

        cal.add_component(event)

    return cal


def generate_ics_content():
    """Generate iCalendar file content as bytes without writing to disk."""
    print("Scraping Buckhead Butcher Shop classes and events...\n")

    # Scrape event links
    event_links = scrape_event_links()
    print(f"Found {len(event_links)} events\n")

    if not event_links:
        print("No events found!")
        return None

    # Scrape details for each event
    events = []
    for i, event_link in enumerate(event_links, 1):
        try:
            print(f"[{i}/{len(event_links)}] Scraping: {event_link['title']}")
            details = scrape_event_details(event_link["url"])
            events.append(details)
        except Exception as e:
            print(f"    Error: {e}")

    print(f"\nSuccessfully scraped {len(events)} events")

    # Create iCal file
    print("Generating iCal content")
    cal = create_ical(events)

    return cal.to_ical()


def main():
    """Main entry point."""
    print("Scraping Buckhead Butcher Shop classes and events...\n")

    # Scrape event links
    event_links = scrape_event_links()
    print(f"Found {len(event_links)} events\n")

    if not event_links:
        print("No events found!")
        return

    # Scrape details for each event
    events = []
    for i, event_link in enumerate(event_links, 1):
        try:
            print(f"[{i}/{len(event_links)}] Scraping: {event_link['title']}")
            details = scrape_event_details(event_link["url"])
            events.append(details)
        except Exception as e:
            print(f"    Error: {e}")

    print(f"\nSuccessfully scraped {len(events)} events")

    # Create iCal file
    print(f"\nGenerating iCal file: {OUTPUT_FILE}")
    cal = create_ical(events)

    with open(OUTPUT_FILE, "wb") as f:
        f.write(cal.to_ical())

    print(f"Done! Calendar saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
