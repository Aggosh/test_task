import json
import requests
import sys

import db


from urllib.error import HTTPError
from urllib.parse import quote


API_KEY = str(sys.argv[1])


API_HOST = "https://api.yelp.com"
SEARCH_PATH = "/v3/businesses/search"
BUSINESS_PATH = "/v3/businesses/"


DEFAULT_TERM = str(sys.argv[2])
DEFAULT_LOCATION = str(sys.argv[3])
SEARCH_LIMIT = int(sys.argv[4])


def request(host: str, path: str, api_key: str, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = "{0}{1}".format(host, quote(path.encode("utf8")))
    headers = {
        "Authorization": "Bearer %s" % api_key,
    }

    response = requests.request("GET", url, headers=headers, params=url_params)

    return response.json()


def search(api_key: str, term: str, location: str):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        "term": term.replace(" ", "+"),
        "location": location.replace(" ", "+"),
        "limit": SEARCH_LIMIT,
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def get_business(api_key: str, business_id: str):
    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, api_key)


def query_api(term: str, location: str):
    """Queries the API by the input values from the user.
    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    response = search(API_KEY, term, location)

    businesses = response.get("businesses")

    return businesses


def get_google_rating(query: str):
    """Query the Google rating .
    Args:
        query (str): search query.
    Returns:
        float or "NULL": The float or "NULL" response from the request.
    """
    response = requests.get(
        f'https://www.google.com/search?&q={query.replace(" ", "+")}'
    )

    n1 = response.text.find('" aria-hidden="true">')
    n2 = response.text.find('</span> <div class="', n1)

    if len(response.text[n1 + 16 : n2]) > 30:
        return "NULL"

    return float(response.text[n1 + 21 : n2].replace(",", "."))


def get_website(url: str):
    """Query the Yelp rating .
    Args:
        url (str): search Yelp url.
    Returns:
        float or "NULL": The float or "NULL" response from the request.
    """
    response = requests.get(url)

    n1 = response.text.find('","linkText":"')
    n2 = response.text.find('"', n1 + 14)

    if len(response.text[n1 + 14 : n2]) > 30:
        n1 = response.text.find('", "linkText": "')
        n2 = response.text.find('"', n1 + 16)
        if len(response.text[n1 + 16 : n2]) > 30:
            return "NULL"
        return response.text[n1 + 16 : n2]

    return response.text[n1 + 14 : n2]


def main():
    try:
        restaurants = query_api(DEFAULT_TERM, DEFAULT_LOCATION)
    except HTTPError as error:
        sys.exit(
            "Encountered HTTP error {0} on {1}:\n {2}\nAbort program.".format(
                error.code,
                error.url,
                error.read(),
            )
        )

    database = db.DataBase()
    database.crete_table()

    for restaurant in restaurants:
        tags = []
        for tag in restaurant.get("categories"):
            tags.append(tag.get("title"))

        google_rating = get_google_rating(
            f'{restaurant.get("name")} {restaurant.get("location").get("address1")} restaurant.get("location").get("city")'
        )

        website = get_website(restaurant.get("url"))
        print("Google:", google_rating)
        print("Website:", website)

        database.insert_restaurant(
            restaurant.get("name").replace("'", ""),
            telephone=restaurant.get("phone"),
            website=website,
            address=restaurant.get("location").get("address1").replace("'", ""),
            city=restaurant.get("location").get("city").replace("'", ""),
            zip_code=restaurant.get("location").get("zip_code"),
            latitude=restaurant.get("coordinates").get("latitude"),
            longitude=restaurant.get("coordinates").get("longitude"),
            yelp_rating=restaurant.get("rating"),
            google_rating=google_rating,
            tags=tags,
        )


if __name__ == "__main__":
    main()
