import requests
import grequests
import time
import json

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


def build_request(business_name, location):
    params = {'location': location, 'term': business_name}
    url = 'https://api.yelp.com/v3/businesses/search'
    return grequests.get(url=url, params=params, headers=headers)


def process_response(resp, business_name, location):
    response_time = time.time()
    try:
        top_businesses = resp.json()['businesses']
        for i in range(len(top_businesses)):
            b1 = (top_businesses[i]['name']).lower()
            b2 = business_name.lower()
            a1 = (top_businesses[i]['location']['address1']).lower()
            a2 = location.lower()

            # immediately return business with 2 matches
            if (b1 == b2) and (a1 == a2):
                return top_businesses[i]
            # save business with one match
            if (b1 == b2) or (a1 == a2):
                tmp = top_businesses[i]
        # return business with one match
        print "response time is", time.time() - response_time, "seconds"
        return tmp

    except:
        print "response time is", time.time() - response_time, "seconds"
        return []


def get_yelp_shit():
    with open("jsons/kardashian-transcripts.json") as df:
        restaurants = json.load(df)["business_id_to_name"]

    keys = restaurants.keys()

    names = []
    adds = []
    reqs = []

    api_time = time.time()
    for k in keys:
        info = restaurants[k]
        name = info[0]
        full_address = info[3]
        names.append(name)
        adds.append(full_address)

        request = build_request(name, full_address)
        reqs.append(request)
    print "Building requests takes", time.time() - api_time, "seconds"

    make_requests_time = time.time()
    results = grequests.map(reqs)
    print "map time was", time.time() - make_requests_time, "seconds"
    res = [process_response(extra, names[i], adds[i]) for i, extra in enumerate(results) if extra != []]
    print "Making requests takes", time.time() - make_requests_time, "seconds"

    # Associate keys with data
    new_map = {}
    for i, k in enumerate(keys):
        new_map[k] = res[i]

    print "New map has", len(new_map), "elements"
    with open("business_id_to_restaurant_data.json", "w") as df:
        json.dump(new_map, df)

    return res


if __name__ == "__main__":
    get_yelp_shit()
