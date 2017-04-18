from .models import Docs
import os
import Levenshtein
import json

from collections import defaultdict
from helpers import sort_dict_by_val


def read_file(n):
    path = Docs.objects.get(id=n).address
    file = open(path)
    transcripts = json.load(file)
    return transcripts


def _edit(query, msg):
    return Levenshtein.distance(query.lower(), msg.lower())


def get_ordered_cities():
    cities = defaultdict(int)
    with open('yelp_data/yelp_academic_dataset_business.json') as data_file:
        for line in data_file:
            data = json.loads(line)
            cities[data['city']] += 1
    dests = sort_dict_by_val(cities)[:10]

    dests = sorted(dests)
    homes = sorted(cities.keys())
    return dests, homes


def find_similar(q):
    transcripts = read_file(1)
    result = []
    for transcript in transcripts:
        for item in transcript:
            m = item['text']
            result.append(((_edit(q, m)), m))

    return sorted(result, key=lambda tup: tup[0])
