#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .models import Docs
import os
import json
import numpy as np
import Levenshtein
from collections import defaultdict
from helpers import sort_dict_by_val
import requests


# YELP API
app_id = 'xGJw03IyUyyPy4XuNn4h_A'
app_secret = 'HfiPbyE1t1tzH7NkEJ5e1kcG157gw1uQ15BX4YhiQCpJjHyAR34T3AUuP1aU2nz9'
data = {'grant_type': 'client_credentials',
        'client_id': app_id,
        'client_secret': app_secret}
token = requests.post('https://api.yelp.com/oauth2/token', data=data)
access_token = token.json()['access_token']
url = 'https://api.yelp.com/v3/businesses/search'
headers = {'Authorization': 'bearer %s' % access_token}


def api_business_info(business_name, location):
    params = {'location': location, 'term': business_name}
    url = 'https://api.yelp.com/v3/businesses/search'
    resp = requests.get(url=url, params=params, headers=headers)

    try:
        top_businesses = resp.json()['businesses']
        for i in range(len(top_businesses)):
            b1 = (top_businesses[i]['name']).lower()
            b2 = business_name.lower()
            a1 = (top_businesses[i]['location']['address1']).lower()
            a2 = location.lower()
            temp = []
            #immediately return business with 2 matches
            if (b1 == b2) and (a1 == a2):
                return top_businesses[i]
            #save business with one match
            if (b1 == b2) or (a1 == a2):
                tmp = top_businesses[i]
        #return business with one match
        return tmp

    except:
        return []


# k is number of results to display
def find_most_similar(topMatches, unique_ids, business_id_to_name, id1, destCity, contributing_words, k=15):
    """
    Find most similar restaurants to the given restaurant id.

    Accepts: similarity matrix of restauranst, restaurant id.
    Returns: list of (score, restaurant name) tuples for restaurant with id1 sorted by cosine_similarity score
    """
    # rel_index = unique_ids.index(id1)
    # rel_row = sim_matrix[rel_index]
    # print "rel_index: "
    # print rel_index
    # print "destCity: "
    # print destCity
    topMatchesRow = topMatches[id1][destCity]
    # max_indices = np.argpartition(rel_row, -k)[-k:]
    # most_similar_scores_and_ids = [(rel_row[x], business_id_to_name[unique_ids[x]]) for x in max_indices]
    # most_similar_scores_and_ids = sorted(most_similar_scores_and_ids,key=lambda x:-x[0])
    most_similar_ids = [business_id_to_name[x] for x in topMatchesRow][:k]
    # id -> (name,city,state)
    res = []
    res2 = []
    for i in range(len(most_similar_ids)):
        info = most_similar_ids[i]
        name = info[0]
        city = info[1]
        state = info[2]
        full_address = info[3]
        print("topMatchesRow[i]: " + str(topMatchesRow[i]))
        print("contributing_words: " + str(contributing_words))
        words = contributing_words[topMatchesRow[i]]
        extra_info = api_business_info(name, full_address)
        if extra_info != []:
            res.append(extra_info)
        res2.append(words)
    return res, res2


    # return most_similar_scores_and_ids


def get_ordered_cities():
    data = read(1)["cities"]
    # Deal with Montréal and other accent problems here
    for i in range(len(data)):
        data[i] = data[i].replace(u'\xe9', 'e')
    return sorted(data[:10]), (["Search in all cities"] + sorted(data))


def read(n):
    path = Docs.objects.get(id=n).address
    file = open(path)
    data = json.load(file)
    return data


def read_file(n):
    path = Docs.objects.get(id=n).address
    file = open(path)
    data = json.load(file)
    # sim_matrix = data['svd_matrix']
    topMatches = data['topMatches']
    unique_ids = data['unique_ids']
    business_id_to_name = data['business_id_to_name']
    business_name_to_id = data['business_name_to_id']
    contributing_words = data['contributing_words']

    return topMatches, unique_ids, business_id_to_name, business_name_to_id, contributing_words



# responds to request
def find_similar(query,origin,destination):
    print origin,destination
    origin = origin.lower()
    destination = destination.lower()
    query = query.lower() # business_name_to_id.json has all business names in lower case
    topMatches, unique_ids, business_id_to_name, business_name_to_id, contributing_words = read_file(1)
    bestMatchKey = ''
    if query in business_name_to_id:
        bid = business_name_to_id[query][0]
        lists = business_name_to_id[query]
        for i in range(len(lists[0])):
            if lists[1][i] == origin:
                bid = lists[0][i]
                break
        # This if/else block is to deal with the unique_ids problem. Remove it later on
        if bid in unique_ids:
            result, result2 = find_most_similar(topMatches, unique_ids, business_id_to_name, bid, destination, contributing_words[bid])
        else:
            minDist = 999999
            # If query isn't in our business list, find match with lowest edit distance. Change later to choose correct one from list of values (same named restaurants, different cities)
            bestMatchKey = query
            bestMatchBid = ''
            for bid in unique_ids:
                business = business_id_to_name[bid]
                name = business[0]
                city = business[1] # Use this later to restrict search to within origin city. Not using it now because it'll suck with a small dataset
                dist = Levenshtein.distance(name, query)
                if dist < minDist:
                    minDist = dist
                    bestMatchKey = name
                    bestMatchBid = bid
            bid = bestMatchBid
            result, result2 = find_most_similar(topMatches, unique_ids, business_id_to_name, bid, destination, contributing_words[bid])
    else:
        minDist = 999999
        # If query isn't in our business list, find match with lowest edit distance. Change later to choose correct one from list of values (same named restaurants, different cities)
        bestMatchKey = query
        bestMatchBid = ''
        for bid in unique_ids:
            business = business_id_to_name[bid]
            name = business[0]
            city = business[1] # Use this later to restrict search to within origin city. Not using it now because it'll suck with a small dataset
            dist = Levenshtein.distance(name, query)
            if dist < minDist:
                minDist = dist
                bestMatchKey = name
                bestMatchBid = bid
        # This code should work once we're using the complete dataset. But commented out and using simpler version for now for prototype
        # for key, value in business_name_to_id.iteritems():
        #     if origin in value[1]:
        #         idx = value[1].indexOf(origin)
        #         dist = Levenshtein.distance(query, key)
        #         if dist < minDist:
        #             minDist = dist
        #             bestMatchKey = key
        #             bestMatchBid = value[0][i]
        bid = bestMatchBid
        result, result2 = find_most_similar(topMatches, unique_ids, business_id_to_name, bid, destination, contributing_words[bid])

    return result, bestMatchKey, result2


# print (api_business_info("Pizza Pizza", '979 Bloor Street W'))
# print (api_business_info("Plush Salon and Spa", '7014 Steubenville Pike'))
# print (api_business_info("Comfort Inn", '321 Jarvis Street'))