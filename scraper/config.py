"""UMaine sports configuration."""

GOBLACKBEARS_BASE = "https://goblackbears.com"
AMERICA_EAST_BASE = "https://americaeast.com"
HOCKEY_EAST_BASE = "https://www.hockeyeastonline.com"

# Priority sports shown in featured strip at top of page
PRIORITY_SPORTS = ["mhockey", "wbball", "mbball", "football"]

SPORTS = [
    {"sport": "Men's Ice Hockey", "shortname": "mhockey", "sport_id": 7, "slug": "mens-ice-hockey", "conference": "hockey_east", "ae_path": None},
    {"sport": "Women's Ice Hockey", "shortname": "whockey", "sport_id": 13, "slug": "womens-ice-hockey", "conference": "hockey_east", "ae_path": None},
    {"sport": "Football", "shortname": "football", "sport_id": 3, "slug": "football", "conference": "america_east", "ae_path": None},
    {"sport": "Men's Basketball", "shortname": "mbball", "sport_id": 5, "slug": "mens-basketball", "conference": "america_east", "ae_path": "mbball"},
    {"sport": "Women's Basketball", "shortname": "wbball", "sport_id": 11, "slug": "womens-basketball", "conference": "america_east", "ae_path": "wbball"},
    {"sport": "Baseball", "shortname": "baseball", "sport_id": 1, "slug": "baseball", "conference": "america_east", "ae_path": "baseball"},
    {"sport": "Softball", "shortname": "softball", "sport_id": 10, "slug": "softball", "conference": "america_east", "ae_path": "softball"},
    {"sport": "Field Hockey", "shortname": "fhockey", "sport_id": 2, "slug": "field-hockey", "conference": "america_east", "ae_path": "fhockey"},
    {"sport": "Women's Soccer", "shortname": "wsoc", "sport_id": 14, "slug": "womens-soccer", "conference": "america_east", "ae_path": "wsoc"},
    {"sport": "Men's Swimming & Diving", "shortname": "mswim", "sport_id": None, "slug": "mens-swimming-and-diving", "conference": "america_east", "ae_path": None},
    {"sport": "Women's Swimming & Diving", "shortname": "wswim", "sport_id": None, "slug": "womens-swimming-and-diving", "conference": "america_east", "ae_path": None},
    {"sport": "Men's Cross Country", "shortname": "mcross", "sport_id": None, "slug": "mens-cross-country", "conference": "america_east", "ae_path": None},
    {"sport": "Women's Cross Country", "shortname": "wcross", "sport_id": None, "slug": "womens-cross-country", "conference": "america_east", "ae_path": None},
    {"sport": "Men's Track & Field", "shortname": "mtrack", "sport_id": None, "slug": "mens-track-and-field", "conference": "america_east", "ae_path": None},
    {"sport": "Women's Track & Field", "shortname": "wtrack", "sport_id": None, "slug": "womens-track-and-field", "conference": "america_east", "ae_path": None},
]

BDN_BASE = "https://www.bangordailynews.com"
BDN_SPORTS_FEEDS = [
    "/category/sports/college-ice-hockey/feed/",
    "/category/sports/college-basketball/feed/",
    "/category/sports/college-football/feed/",
    "/category/sports/feed/",
]

USER_AGENT = "BDNUMaineSports/1.0 (bangordailynews.com)"
