import json

from nested_lookup import nested_lookup
import requests
import requests_cache
import xmltodict


requests_cache.install_cache("dev_cache")


episode_tags = [
    "category",
    "description",
    "guid",
    "itunes:block",
    "itunes:duration",
    "itunes:episode",
    "itunes:episodeType",
    "itunes:explicit",
    "itunes:keywords",
    "itunes:season",
    "itunes:subtitle",
    "itunes:title",
    "link",
    "pubDate",
    "title",
]

podcast_tags = [
    "copyright",
    "creativeCommons:license",
    "cover art",
    "description",
    "generator",
    "itunes:author",
    "itunes:block",
    "itunes:category",
    "itunes:complete",
    "itunes:explicit",
    "itunes:image",
    "itunes:keywords",
    "itunes:owner",
    "itunes:new-feed-url",
    "itunes:subtitle",
    "itunes:title",
    "itunes:type",
    "language",
    "lastBuildDate",
    "link",
    "managingEditor",
    "pubDate",
    "webMaster",
    "title",
    "url",
]


def get_categories(channel):
    raw_categories = channel.get("itunes:category", None)
    categories = nested_lookup("@text", raw_categories)
    return categories


def get_enclosure(item):
    raw_enclosure = item.get("enclosure", None)
    if raw_enclosure is None:
        return None
    enclosure = {}
    enclosure["length"] = raw_enclosure.get("@length", None)
    enclosure["type"] = raw_enclosure.get("@type", None)
    enclosure["url"] = raw_enclosure.get("@url", None)
    return enclosure


def get_item(item):
    item_dict = {}
    for tag in episode_tags:
        item_dict[tag] = item.get(tag, None)

    item_dict["enclosure"] = get_enclosure(item)
    item_dict["guid"] = item.get("guid", None).get("#text", None)
    try:
        item_dict["itunes:image"] = item["itunes:image"]["@href"]
    except KeyError:
        item_dict["itunes:image"] = None

    return item_dict


def get_items(channel):
    items = []
    for each in channel.get("item", None):
        item = get_item(each)
        items.append(item)
    return items


def podcast_to_dict(url):
    podcast_dict = {}
    r = requests.get(url)
    podcast_dict["url"] = r.url
    parsed_xml = xmltodict.parse(r.text)
    channel = parsed_xml["rss"]["channel"]
    for tag in podcast_tags:
        podcast_dict[tag] = channel.get(tag, None)
    podcast_dict["itunes:category"] = get_categories(channel)
    podcast_dict["items"] = get_items(channel)
    podcast_dict["itunes:image"] = channel.get("itunes:image", None).get("@href", None)
    podcast_dict["url"] = url

    # print(json.dumps(podcast_dict, sort_keys=True, indent=4))
    return podcast_dict


# url = "https://talktotheleft.libsyn.com/rss"
# podcast_to_dict(url)
