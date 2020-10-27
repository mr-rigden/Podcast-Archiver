from datetime import date
import json
import os
from os.path import join
from urllib import parse as urlparse
from urllib.parse import urlparse

import xml

import click
from jinja2 import Environment, FileSystemLoader
import requests
from slugify import slugify

import requests
import requests_cache

requests_cache.install_cache("dev_cache")

from podcast_to_dict import podcast_to_dict

home_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(home_dir, "output")

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader, extensions=["jinja2.ext.loopcontrols"])
env.globals["slugify"] = slugify


def download_coverart(podcast_dict):
    podcast_dir = os.path.join(output_dir, slugify(podcast_dict["title"]))
    header = requests.head(podcast_dict["itunes:image"], allow_redirects=True)
    file_name = os.path.basename(urlparse(header.url).path)
    file_path = os.path.join(podcast_dir, "img", file_name)
    if os.path.exists(file_path):
        return file_name
    r = requests.get(podcast_dict["itunes:image"], allow_redirects=True)
    open(file_path, "wb").write(r.content)
    return file_name


def download_audio_file(url, podcast_dir):
    header = requests.head(url, allow_redirects=True)
    file_name = os.path.basename(urlparse(header.url).path)
    file_path = os.path.join(podcast_dir, "audio", file_name)
    if os.path.exists(file_path):
        return file_name
    r = requests.get(url, allow_redirects=True)
    open(file_path, "wb").write(r.content)
    return file_name


def make_dirs(podcast_dict):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    podcast_dir = os.path.join(output_dir, slugify(podcast_dict["title"]))
    if not os.path.exists(podcast_dir):
        os.makedirs(podcast_dir)

    audio_dir = os.path.join(podcast_dir, "audio")
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    audio_dir = os.path.join(podcast_dir, "img")
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    episode_dir = os.path.join(podcast_dir, "episode")
    if not os.path.exists(episode_dir):
        os.makedirs(episode_dir)


def render_json(podcast_dict):
    slug = slugify(podcast_dict["title"])
    file_name = slug + ".json"
    file_path = os.path.join(output_dir, slug, file_name)
    print(file_path)

    with open(file_path, "w") as f:
        f.write(json.dumps(podcast_dict, sort_keys=True, indent=4))


def render_episode(episode, podcast_dict):
    podcast_dir = os.path.join(output_dir, slugify(podcast_dict["title"]))
    file_name = slugify(episode["title"]) + ".html"
    file_path = os.path.join(podcast_dir, "episode", file_name)

    if os.path.exists(file_path):
        return file_name

    episode["audio_file"] = download_audio_file(
        episode["enclosure"]["url"], podcast_dir
    )
    print(episode["audio_file"])

    template = env.get_template("episode.html")
    output = template.render(episode=episode, podcast_dict=podcast_dict)
    with open(file_path, "w") as f:
        f.write(output)


def render_index(podcast_dict):
    file_path = os.path.join(output_dir, slugify(podcast_dict["title"]), "index.html")
    template = env.get_template("list.html")
    output = template.render(podcast_dict=podcast_dict)
    with open(file_path, "w") as f:
        f.write(output)


def update_root_dir():
    podcasts = []
    dir_contents = os.scandir(output_dir)
    for each in dir_contents:
        if os.path.isdir(each):
            file_path = os.path.join(output_dir, each.name, (each.name + ".json"))
            try:
                with open(file_path) as f:
                    data = json.load(f)
            except FileNotFoundError:
                continue
            podcast = {}
            podcast["title"] = data["title"]
            podcast["slug"] = each.name
            podcasts.append(podcast)
    file_path = os.path.join(output_dir, "index.html")
    template = env.get_template("root.html")
    output = template.render(podcasts=podcasts)
    with open(file_path, "w") as f:
        f.write(output)


@click.command()
@click.option("--url", help="URL of Podcast RSS Feed", required=True)
def archive_podcast(url):
    print("Attemting to archive: " + url)
    try:
        podcast_dict = podcast_to_dict(url)
    except requests.exceptions.MissingSchema:
        print("   ERROR: Invalid URL: Missing Schema")
        exit()
    except requests.exceptions.ConnectionError:
        print("    ERROR: Could not connect to URL")
        exit()
    except xml.parsers.expat.ExpatError:
        print("    ERROR: Bad XML")
        exit()
    podcast_dict["archived"] = date.today().strftime("%B %d, %Y")
    make_dirs(podcast_dict)
    render_index(podcast_dict)
    render_json(podcast_dict)
    podcast_dict["cover art"] = download_coverart(podcast_dict)
    for episode in podcast_dict["items"]:
        render_episode(episode, podcast_dict)
    update_root_dir()


if __name__ == "__main__":
    archive_podcast()
