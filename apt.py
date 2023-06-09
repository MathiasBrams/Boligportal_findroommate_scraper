from selenium import webdriver
from bs4 import BeautifulSoup
import json 
from time import sleep
import os
os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')
import vlc 
from tqdm import tqdm  
from selenium.webdriver.chrome.options import Options


# APT_URL = 'https://www.boligportal.dk/find?placeIds=76%2C75%2C2100%2C3921&minRooms=3'
# APT_URL = 'https://www.boligportal.dk/v%C3%A6relser,lejligheder/k%C3%B8benhavn'
APT_URL = 'https://www.boligportal.dk/v%C3%A6relser,lejligheder/k%C3%B8benhavn/?max_monthly_rent=4500'
ROOMMATE_URL = 'https://www.findroommate.dk/vaerelser/koebenhavn'

seen_apartments = {}
seen_rooms = {}

MAX_PRICE = 5001


def get_apartment_str(title, location, price, url): 
    return f'{title}-{location}-{price}-{url}'


def new_apartments(apartments, isFindMyRoomMate = False): 
    new_apartments = []
    for title, location, price, url in apartments: 

        if url not in seen_apartments and price < MAX_PRICE: 
            if url not in seen_rooms:
                new_apartments.append((title, location, price, url))

        if(isFindMyRoomMate):
            seen_rooms[url] = {
                'title': title, 
                'location': location, 
                'price': price
            }
        else:
            seen_apartments[url] = {
                'title': title, 
                'location': location, 
                'price': price
            }
            
    
    return new_apartments


def print_apartment(title, location, price, url, isFindMyRoomMate = False): 
    if(isFindMyRoomMate):
        url = f'https://www.findroommate.dk{url}'
    else:
        url = f'https://www.boligportal.dk{url}'

    bottom_line_length = len(url)
    bottom_line = ''.join(['-' for _ in range(bottom_line_length)])
    bottom_line = f'--|----{bottom_line}'

    title_line = f'--|--- {title}'
    title_line_missing = len(bottom_line) - len(title_line) - 1
    title_line += ' '
    title_line += ''.join(['-' for _ in range(title_line_missing)])
    
    print()
    print(f'{title_line}')
    print(f'  |    kr. {price}')
    print(f'  |    {location}')
    print(f'  |    {url}')
    print(f'{bottom_line}')
    print()


if __name__ == '__main__': 

    with open('apartments.json') as fp: 
        seen_apartments = json.load(fp)

    with open('rooms.json') as rp: 
        seen_rooms = json.load(rp)

    while True:
        # code for BOLIGPORTALEN 
        try:
            print(f'Fetching BOLIGPORTALEN pages...')
            chrome_options = Options()
            # chrome_options.add_argument("--no-sandbox") # linux only
            chrome_options.add_argument("--headless")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # Get the URL and execute the JavaScript so we have the contents
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(APT_URL)
            rendered_source = driver.page_source

            # Soupify the contents
            soup = BeautifulSoup(rendered_source, features="html.parser")

            # Get all the ad_cards on the page
            ad_cards = soup.find_all('a', {'class': ['AdCard', 'AdCardSrp__Link css-1gsgxxt']})

            print(len(ad_cards))
            # print(soup)
            # print(ad_cards[0].find_all('div', {'class': ['css-5oox4j']})[0].decode_contents())
            # Extract the title, location, and price of all ad cards
            titles = [card.find_all('div', {'class': ['css-5oox4j']})[0].decode_contents() for card in ad_cards]
            locations = [card.find_all('div', {'class': ['css-22506a']})[0].decode_contents() for card in ad_cards]
            prices = [card.find_all('span', {'class': ['css-1wltohh']})[0].decode_contents() for card in ad_cards]
            prices = [int(price.replace(',-', '').replace('.', '').replace('\xa0kr','').strip()) for price in prices]
            urls = [card['href'] for card in ad_cards]

            # Construct apartment objects
            apartments = zip(titles, locations, prices, urls)

            if unseen_apartments := new_apartments(apartments): 
                # Play sound
                p = vlc.MediaPlayer("done-for-you.mp3")
                p.play()

                # Print the apartments
                for title, location, price, url in unseen_apartments: 
                    print_apartment(title, location, price, url)
                    
                
                with open('apartments.json', 'w+') as fp: 
                    json.dump(seen_apartments, fp, indent=True, ensure_ascii=True)
            
            # for _ in tqdm(range(60), desc='Waiting before refresh...'): 
            #     sleep(1)

        except Exception as err: 
            print(err)
            sleep(5)
        #     # continue



        # code for FINDROOMMATE 
        try:
            print(f'Fetching FINDROOMMATE pages...')
            chrome_options = Options()
            # chrome_options.add_argument("--no-sandbox") # linux only
            chrome_options.add_argument("--headless")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # Get the URL and execute the JavaScript so we have the contents
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(ROOMMATE_URL)
            rendered_source = driver.page_source

            # Soupify the contents
            soup = BeautifulSoup(rendered_source, features="html.parser")

            # Get all the ad_cards on the page
            # ad_cards = soup.find_all('a')
            ad_cards = soup.find_all('div', {'class': ['roomListing']})

            print(len(ad_cards))
            # print(ad_cards[0])
            # print(ad_cards[0].find_all('div', {'class': ['css-5oox4j']})[0].decode_contents())
            # Extract the title, location, and price of all ad cards
            titles = [card.find_all('div', {'class': ['roomBaseInfo']})[0].decode_contents() for card in ad_cards]
            locations = [card.find_all('div', {'class': ['roomCity']})[0].decode_contents() for card in ad_cards]
            prices = [card.find_all('div', {'class': ['roomRent']})[0].decode_contents() for card in ad_cards]
            prices = [int(price.replace(',-', '').replace('.', '').replace(' kr/md','').strip()) for price in prices]
            urls = []
            aElements = [card.find_all('a')[0].decode_contents() for card in ad_cards]

            for card in ad_cards:
                for a in card.find_all('a'):
                    urls.append(a['href'])

            # Construct apartment objects
            apartments = zip(titles, locations, prices, urls)

            if unseen_apartments := new_apartments(apartments, True): 
                # Play sound
                p = vlc.MediaPlayer("done-for-you.mp3")
                p.play()

                # Print the apartments
                for title, location, price, url in unseen_apartments: 
                    print_apartment(title, location, price, url, True)
                    
                
                with open('rooms.json', 'w+') as rp: 
                    json.dump(seen_rooms, rp, indent=True, ensure_ascii=True)
            
            for _ in tqdm(range(60), desc='Waiting before refresh...'): 
                sleep(1)

        except Exception as err: 
            print(err)
            sleep(5)
            continue

