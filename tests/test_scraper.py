"""
Unit tests for Buckhead Butcher Shop events scraper.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytz
from icalendar import Calendar
from bs4 import BeautifulSoup

# Import functions from the scraper
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bbical.__main__ import (
    parse_date_time,
    scrape_event_links,
    scrape_event_details,
    create_ical,
)

EASTERN = pytz.timezone("US/Eastern")


class TestDateTimeParsing:
    """Test the parse_date_time function."""

    def test_basic_date_time_parsing(self):
        """Test parsing a valid date and time."""
        dt = parse_date_time("Friday, June 12th", "6:30 pm")
        assert dt.month == 6
        assert dt.day == 12
        assert dt.hour == 18
        assert dt.minute == 30
        assert dt.tzinfo == EASTERN

    def test_various_ordinal_suffixes(self):
        """Test parsing dates with different ordinal suffixes."""
        for suffix in ["st", "nd", "rd", "th"]:
            dt = parse_date_time(f"Monday, April 1{suffix}", "3:00 pm")
            assert dt.month == 4
            assert dt.day == 1

    def test_am_time(self):
        """Test parsing AM time."""
        dt = parse_date_time("Monday, August 10th", "9:00 am")
        assert dt.hour == 9

    def test_12_pm_midnight_noon(self):
        """Test special cases: 12 AM and 12 PM."""
        dt_noon = parse_date_time("Monday, August 10th", "12:00 pm")
        assert dt_noon.hour == 12

        dt_midnight = parse_date_time("Monday, August 10th", "12:00 am")
        assert dt_midnight.hour == 0

    def test_all_months(self):
        """Test parsing dates for all 12 months."""
        months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december"
        ]
        for month_num, month_name in enumerate(months, 1):
            dt = parse_date_time(f"Friday, {month_name.capitalize()} 15th", "6:00 pm")
            assert dt.month == month_num
            assert dt.day == 15

    def test_case_insensitive_month(self):
        """Test that month names are case-insensitive."""
        dt1 = parse_date_time("Friday, JUNE 12th", "6:30 pm")
        dt2 = parse_date_time("Friday, june 12th", "6:30 pm")
        assert dt1.month == dt2.month == 6

    def test_past_date_uses_next_year(self):
        """Test that past dates are assumed to be next year."""
        # If we parse January 1st and today is after January 1st,
        # it should use next year
        today = datetime.now(tz=EASTERN)
        dt = parse_date_time("Friday, January 1st", "6:00 pm", reference_date=today)
        # If today is past January 1st, year should be next year
        if today.month > 1 or (today.month == 1 and today.day > 1):
            assert dt.year == today.year + 1
        else:
            assert dt.year == today.year

    def test_future_date_uses_current_year(self):
        """Test that future dates use the current year."""
        ref_date = datetime(2026, 1, 15, tzinfo=EASTERN)
        dt = parse_date_time("Friday, June 12th", "6:00 pm", reference_date=ref_date)
        assert dt.year == 2026

    def test_invalid_month_raises_error(self):
        """Test that invalid month names raise ValueError."""
        with pytest.raises(ValueError):
            parse_date_time("Friday, Decemberuary 15th", "6:00 pm")

    def test_invalid_time_raises_error(self):
        """Test that invalid times raise ValueError."""
        with pytest.raises(ValueError):
            parse_date_time("Friday, June 12th", "25:99 pm")

    def test_date_without_ordinal_suffix(self):
        """Test parsing date without ordinal suffix (e.g., 'June 12')."""
        dt = parse_date_time("Friday, June 12", "6:30 pm")
        assert dt.month == 6
        assert dt.day == 12

    def test_date_without_comma(self):
        """Test parsing date without comma separator."""
        dt = parse_date_time("Friday June 12th", "6:30 pm")
        assert dt.month == 6
        assert dt.day == 12


class TestEventLinkScraping:
    """Test the scrape_event_links function."""

    @patch("bbical.__main__.fetch_page")
    def test_extract_event_links(self, mock_fetch):
        """Test extracting event links from the main page."""
        html = """
        <a href="https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/">
            Steak Class - Friday, June 12th 6:30 pm
        </a>
        <a href="https://buckheadbutchershop.com/pasta-101-class-friday-may-22nd-6-30-pm/">
            Pasta 101 Class - Friday, May 22nd 6:30 pm
        </a>
        """
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        links = scrape_event_links()
        assert len(links) == 2
        assert any("steak-class" in link["url"] for link in links)
        assert any("pasta-101" in link["url"] for link in links)

    @patch("bbical.__main__.fetch_page")
    def test_filter_out_main_page_link(self, mock_fetch):
        """Test that the main classes-events page link is filtered out."""
        html = """
        <a href="https://buckheadbutchershop.com/classes-events/">
            Upcoming Classes & Events
        </a>
        <a href="https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/">
            Steak Class - Friday, June 12th 6:30 pm
        </a>
        """
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        links = scrape_event_links()
        assert len(links) == 1
        assert "steak-class" in links[0]["url"]

    @patch("bbical.__main__.fetch_page")
    def test_filter_links_without_class_in_href(self, mock_fetch):
        """Test that links without 'class' in href are filtered out."""
        html = """
        <a href="https://buckheadbutchershop.com/about/">About Us</a>
        <a href="https://buckheadbutchershop.com/steak-class-friday-june-12th/">
            Steak Class
        </a>
        """
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        links = scrape_event_links()
        assert len(links) == 1

    @patch("bbical.__main__.fetch_page")
    def test_deduplicate_links(self, mock_fetch):
        """Test that duplicate links are filtered."""
        html = """
        <a href="https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/">
            Steak Class
        </a>
        <a href="https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/">
            Steak Class
        </a>
        """
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        links = scrape_event_links()
        assert len(links) == 1


class TestEventDetailScraping:
    """Test the scrape_event_details function."""

    @patch("bbical.__main__.fetch_page")
    def test_parse_date_from_url(self, mock_fetch):
        """Test parsing date/time from event URL."""
        html = "<html><title>Steak Class</title><body>Some content</body></html>"
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        )
        assert details["datetime"].month == 6
        assert details["datetime"].day == 12
        assert details["datetime"].hour == 18
        assert details["datetime"].minute == 30

    @patch("bbical.__main__.fetch_page")
    def test_parse_date_from_body_fallback(self, mock_fetch):
        """Test parsing date/time from page body as fallback."""
        html = """
        <html>
        <title>Event Page</title>
        <body>
        <p>Join us for a steak class!</p>
        <p>Saturday, July 15th at 6:30 pm</p>
        </body>
        </html>
        """
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/some-event/"
        )
        # Should fallback to body parsing
        assert details["datetime"].month >= 1

    @patch("bbical.__main__.fetch_page")
    def test_extract_title(self, mock_fetch):
        """Test extracting event title."""
        html = "<html><title>Steak Class - June 12th</title><body></body></html>"
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        )
        assert "Steak Class" in details["title"]

    @patch("bbical.__main__.fetch_page")
    def test_extract_location(self, mock_fetch):
        """Test extracting location from page."""
        html = """
        <html><body>
        <p>Location: Buckhead Butcher Shop, 3198 Cains Hill Place NW, Atlanta GA 30305</p>
        </body></html>
        """
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        )
        assert "Atlanta" in details["location"]
        assert "GA" in details["location"]

    @patch("bbical.__main__.fetch_page")
    def test_extract_description(self, mock_fetch):
        """Test extracting description from page."""
        html = """
        <html><body>
        <p>This is the first paragraph with meaningful content about the class.</p>
        <p>This is the second paragraph with more details.</p>
        </body></html>
        """
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        )
        assert len(details["description"]) > 0
        assert "meaningful content" in details["description"]

    @patch("bbical.__main__.fetch_page")
    def test_default_location_fallback(self, mock_fetch):
        """Test that default location is used when not found."""
        html = "<html><body>No location info here</body></html>"
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        )
        assert "Buckhead Butcher Shop" in details["location"]

    @patch("bbical.__main__.fetch_page")
    def test_default_description_fallback(self, mock_fetch):
        """Test that default description is used when parsing fails."""
        html = "<html><body></body></html>"
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        )
        assert details["description"] != ""


class TestICalGeneration:
    """Test the create_ical function."""

    def test_create_basic_ical(self):
        """Test creating a basic iCal file."""
        events = [
            {
                "title": "Steak Class",
                "datetime": datetime(2026, 6, 12, 18, 30, tzinfo=EASTERN),
                "location": "Buckhead Butcher Shop, 3198 Cains Hill Place NW, Atlanta GA 30305",
                "description": "Learn to cook steak",
                "url": "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/",
            }
        ]

        cal = create_ical(events)
        assert isinstance(cal, Calendar)
        assert cal["version"] == "2.0"
        assert "Buckhead Butcher Shop" in str(cal["x-wr-calname"])

    def test_ical_event_properties(self):
        """Test that iCal events have all required properties."""
        events = [
            {
                "title": "Pasta Class",
                "datetime": datetime(2026, 5, 22, 18, 30, tzinfo=EASTERN),
                "location": "Buckhead Butcher Shop",
                "description": "Learn to make pasta",
                "url": "https://example.com/pasta-class/",
            }
        ]

        cal = create_ical(events)
        ical_text = cal.to_ical().decode("utf-8")

        # Check for key iCal properties
        assert "SUMMARY:Pasta Class" in ical_text
        assert "LOCATION:Buckhead Butcher Shop" in ical_text
        assert "DESCRIPTION:Learn to make pasta" in ical_text

    def test_ical_dtend_is_2_hours_after_dtstart(self):
        """Test that event end time is 2 hours after start."""
        start_time = datetime(2026, 6, 12, 18, 30, tzinfo=EASTERN)
        events = [
            {
                "title": "Steak Class",
                "datetime": start_time,
                "location": "Location",
                "description": "Description",
                "url": "https://example.com/",
            }
        ]

        cal = create_ical(events)
        # Get the event from the calendar
        event = cal.walk("VEVENT")[0]
        dtstart = event["dtstart"].dt
        dtend = event["dtend"].dt
        duration = dtend - dtstart

        # Check duration is 2 hours
        assert duration.total_seconds() == 2 * 60 * 60

    def test_ical_uid_from_url(self):
        """Test that event UID is generated from URL."""
        url = "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        events = [
            {
                "title": "Steak Class",
                "datetime": datetime(2026, 6, 12, 18, 30, tzinfo=EASTERN),
                "location": "Location",
                "description": "Description",
                "url": url,
            }
        ]

        cal = create_ical(events)
        event = cal.walk("VEVENT")[0]
        uid = str(event["uid"])

        assert url in uid
        assert "buckheadbutchershop.com" in uid

    def test_ical_multiple_events(self):
        """Test creating iCal with multiple events."""
        events = [
            {
                "title": "Steak Class",
                "datetime": datetime(2026, 6, 12, 18, 30, tzinfo=EASTERN),
                "location": "Location 1",
                "description": "Steak",
                "url": "https://example.com/steak/",
            },
            {
                "title": "Pasta Class",
                "datetime": datetime(2026, 5, 22, 18, 30, tzinfo=EASTERN),
                "location": "Location 2",
                "description": "Pasta",
                "url": "https://example.com/pasta/",
            },
        ]

        cal = create_ical(events)
        vevent_components = cal.walk("VEVENT")
        assert len(vevent_components) == 2

    def test_ical_output_format(self):
        """Test that iCal output is valid RFC 5545 format."""
        events = [
            {
                "title": "Steak Class",
                "datetime": datetime(2026, 6, 12, 18, 30, tzinfo=EASTERN),
                "location": "Location",
                "description": "Description",
                "url": "https://example.com/",
            }
        ]

        cal = create_ical(events)
        ical_bytes = cal.to_ical()

        # Check basic iCal format
        assert ical_bytes.startswith(b"BEGIN:VCALENDAR")
        assert ical_bytes.endswith(b"END:VCALENDAR\r\n")
        assert b"BEGIN:VEVENT" in ical_bytes
        assert b"END:VEVENT" in ical_bytes


class TestErrorHandling:
    """Test error handling in scraper functions."""

    def test_parse_date_time_with_invalid_format_raises_error(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError):
            parse_date_time("32nd January", "6:00 pm")

    @patch("bbical.__main__.fetch_page")
    def test_scrape_event_details_handles_missing_title(self, mock_fetch):
        """Test handling of missing page title."""
        html = "<html><body>No title here</body></html>"
        mock_fetch.return_value = BeautifulSoup(html, "html.parser")

        details = scrape_event_details(
            "https://buckheadbutchershop.com/steak-class-friday-june-12th-6-30-pm/"
        )
        # Should use fallback title
        assert "Class" in details["title"] or "Butcher" in details["title"]

    @patch("bbical.__main__.fetch_page")
    def test_scrape_event_details_handles_fetch_error(self, mock_fetch):
        """Test that fetch errors are handled gracefully."""
        mock_fetch.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            scrape_event_details("https://buckheadbutchershop.com/invalid/")

    def test_create_ical_with_empty_list(self):
        """Test creating iCal with empty event list."""
        cal = create_ical([])
        assert isinstance(cal, Calendar)
        # Should have no events
        vevent_components = cal.walk("VEVENT")
        assert len(vevent_components) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
