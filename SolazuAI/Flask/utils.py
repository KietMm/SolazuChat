import requests
def fetch_directory_contents(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        directory_contents = {}
        for item in contents:
            if item['type'] == 'file':
                file_response = requests.get(item['download_url'], headers=headers)
                if file_response.status_code == 200:
                    directory_contents[item['name']] = file_response.text
                else:
                    directory_contents[item['name']] = {'error': 'Failed to fetch file', 'status': file_response.status_code}
            elif item['type'] == 'dir':
                # Make sure only one question mark is used, and parameters are separated by ampersands
                subdir_url = f"{item['url']}&recursive=1"
                directory_contents[item['name']] = fetch_directory_contents(subdir_url, headers)
        return directory_contents
    else:
        print(f"Failed to fetch, URL: {url}, Status Code: {response.status_code}, Response: {response.text}")
        return {'error': f"Failed to fetch directory with status: {response.status_code}"}
