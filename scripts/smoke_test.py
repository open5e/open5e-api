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
    assert requests.get(args.url).status_code == 200 

    # Check the /v1 paths
    assert requests.get(args.url+'/v1/').status_code == 200
    v1_endpoints = requests.get(args.url+'/v1/?format=json').json()
    for value in v1_endpoints.values():
        assert requests.get(value).status_code == 200

    # Checking the /v2 paths
    assert requests.get(args.url+'/v2/').status_code == 200
    v2_endpoints = requests.get(args.url+'/v2/?format=json').json()
    for value in v2_endpoints.values():
        assert requests.get(value).status_code == 200

if __name__ == '__main__':
    main()