import argparse
import requests
# This is the smoke test.

# Inputs: url

# Outputs: Whether any of the basic pages end up in a 500 error.

# Pass if not

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-u', '--url',
        help='URL of the site to check.')

    args = parser.parse_args()
    print("For a given input url, this goes and checks the root, and the /v1 and /v2")
    print("paths for 200 response codes. It is intended to be run post-deploy.")

    # Check the root url.
    results = []
    results.append(check_for_OK(args.url))
    # Check the /v1 paths
    results.append(check_for_OK(args.url+'/v1/'))
    v1_endpoints = requests.get(args.url+'/v1/?format=json').json()
    for value in v1_endpoints.values():
        results.append(check_for_OK(value))

    # Checking the /v2 paths
    results.append(check_for_OK(args.url+'/v2/'))
    v2_endpoints = requests.get(args.url+'/v2/?format=json').json()
    for value in v2_endpoints.values():
        results.append(check_for_OK(value))

    for result in results:
        assert(result,"Path was not OK.")

def check_for_OK(url):
    r = requests.get(url)
    if r.status_code != 200:
        print("Got status {} on {}".format(r.status_code,url))
        return False
    return True


if __name__ == '__main__':
    main()