import requests
from PIL import Image
from io import BytesIO
from lxml import etree
import os
from dotenv import load_dotenv
import browser_cookie3
import getpass
import re

# credit to the mangadex team for making this all possible and providing an amazing service!
# keep in mind that ip gets banned for more than ~500 requests in less than 10 minutes

def downloadChapter(chapter_id, chapter_num, title, session):
    print(f'-----downloading chapter {chapter_num} of {title}-----')
    CHAPTER_API_URL = 'https://mangadex.org/api/?id={}&server=null&saver=0&type=chapter'
    response = session.get(CHAPTER_API_URL.format(chapter_id), headers=HEADERS)
    if response.status_code != 200:
        print(f'request failed for chapter {chapter_id} with status code {response.status_code}, exiting...')
        exit()
    print('---retrived api: success---')

    # download all the pages and add them all to a list
    page_url = response.json()['server'] + response.json()['hash'] + '/'
    im1 = None
    im_list = []
    for page in response.json()['page_array']:
        page_response = requests.get(page_url + page, headers=HEADERS)
        if page_response.status_code != 200:
            print(f'downloading image for page {page} of {chapter_id} failed, exiting...')
            exit()
        print(f'---download {page}: success---')

        temp = Image.open(BytesIO(page_response.content))
        im_list.append(temp.convert('RGB'))
    
    print('---saving chapter---')
    if chapter_num.isdigit():
        filename = '{} - Chapter {:03d}.pdf'.format(title, int(chapter_num))
    else:
        filename = '{} - Chapter {:05.1f}.pdf'.format(title, float(chapter_num))

    im_list[0].save(filename, "PDF", resolution=100.0, save_all=True, append_images=im_list[1:])
    print(f'-----save chapter {chapter_num} of {title}: success-----')

def downloadTitle(title_url, session, lang=1):

    print(f'-----downloading title {title_url}-----')
    response = session.get(title_url, headers=HEADERS)
    if response.status_code != 200:
        print(f'request failed for title at url {title_url} with status code {response.status_code}, exiting...')
        exit()
    
    # path for all the chapter links
    PATH = '//html/body/div[@id="content"]/div[@class="edit tab-content"]/div/div'
    tree = etree.HTML(response.content)
    # name of the manga
    title = tree.xpath('//html/head/meta[@property="og:title"]')[0].get('content').replace(' (Title) - MangaDex', '')
    # the latest chapter available
    latest = float(tree.xpath(PATH)[1].xpath('div/div')[0].get('data-chapter'))

    # check if there are more than one page of the manga
    page_links = tree.xpath('//html/body/div[@id="content"]/div[@class="edit tab-content"]/nav/ul/li[@class="page-item paging"]/a')
    if len(page_links) == 0:
        page_num = 1
    else:
        pattern = re.compile(r'\d+')
        page_num = int(pattern.findall(page_links[0].get('href'))[-1])

    # make a new directory and change into it
    directory = os.path.join('.', title)
    if not title in os.listdir():
        os.makedirs(directory)
    os.chdir(directory)

    # download all the pages
    downloaded = set()
    page_url = f'{title_url}/chapters/'
    for num in range(page_num, 0, -1):
        r = session.get(page_url + str(num), headers=HEADERS)
        if r.status_code != 200:
            print(f'request failed for page at url {page_url}{num} with status code {r.status_code}, exiting...')
            exit()
        t = etree.HTML(r.content)

        # iterate through all the chapters and download them
        node = t.xpath(PATH)
        node.pop(0)
        chapter_num = 0

        # first one need to get the first chapter and prompt for start and end chapter
        if num == page_num:
            first = float(node[-1].xpath('div/div')[0].get('data-chapter'))
            print(f'{title} has chapters from {first} to {latest}, please enter the range you want')
            start_chapter = input(f'start (empty for {first}): ')
            end_chapter = input(f'end (empty for {latest}): ')
            #TODO improve condition checking
            pattern = re.compile(r'^\d+(\.\d+)?$')
            if start_chapter == '':
                start_chapter = str(first)
            if end_chapter == '':
                end_chapter = str(latest)
            
            while not (pattern.match(start_chapter) and pattern.match(end_chapter) and float(start_chapter) <= float(end_chapter) and float(start_chapter) >= 0 and float(end_chapter) >= 0 and float(start_chapter) >= first and float(end_chapter) <= latest):
                print('please input a valid range')
                start_chapter = input(f'start (empty for {first}): ')
                end_chapter = input(f'end (empty for {latest}): ')
                #TODO improve condition checking
                if start_chapter == '':
                    start_chpater = str(first)
                if end_chapter == '':
                    end_chapter = str(latest)
            start_chapter = float(start_chapter)
            end_chapter = float(end_chapter)
        
        # download every chapter
        for i in reversed(node):
            temp = i.xpath('div/div')[0]
            chapter_num = float(temp.get('data-chapter'))
            if chapter_num > end_chapter:
                break
            if chapter_num>=start_chapter:
                if int(temp.get('data-lang')) == lang:
                    downloadChapter(temp.get('data-id'), temp.get('data-chapter'), title, session)
        if chapter_num > end_chapter:
            break

    # go back to the parent directory
    os.chdir(os.path.dirname(os.getcwd()))
    print(f'-----finished downloading all chapters(from {start_chapter} to {chapter_num}) for {title}-----')


# probably impossible due to recaptcha
def login(session):
    login_url = 'https://mangadex.org/ajax/actions.ajax.php?function=login'
    print('please enter your login information')
    username = input('Username: ')
    password = getpass.getpass()
    data = {'login_username': username, 'login_password': password, 'two_factor': ''}
    r = session.post(login_url, data)
    if r.status_code != 200:
        print('login request failed, exiting...')
        exit()

    #check if logged in correctly because you can't tell from the response headers
    tree = etree.HTML(r.content)
    while len(tree.xpath('//html/head/title')) > 0 and 'Login' in tree.xpath('//html/head/title')[0].text:
        print('looks like login failed please try again')
        data['login_username'] = input('Username: ')
        data['login_password'] = getpass.getpass()
        r = session.post(login_url, data)
        tree = etree.HTML(r.content)

# must login in order to search for title
def searchTitle():
    SEARCH_API_URL = 'https://mangadex.org/search?title={}'

    session = requests.Session()
    session.headers.update(HEADERS)

    # TODO: implement login with username and password
    s = input('would you like to get automatically cookies from you browser for login? (y/n) ').lower()
    while s != 'y' and s != 'n' and s != 'yes' and s != 'no':
        s = input('please enter y or n: ').lower()

    if s == 'y' or s == 'yes':
        try: 
            cookies = browser_cookie3.load('mangadex.org')
            session.cookies.update(cookies)
        except:
            print('error loading cookies from mangadex.org')
            login(session)
    else:
        login(session)

    title = input('what manga would you like to download? ')

    response = session.get(SEARCH_API_URL.format(title))
    if response.status_code != 200:
        print(f'requested failed with searching for {title} with status code {response.status_code}, exiting...')
        exit()

    tree = etree.HTML(response.content)
    PATH = '//html/body/div[@id="content"]/div[@class="manga-entry border-bottom"]'
    node = tree.xpath(PATH)
    i = 1
    print('---the following manga are found---')
    for n in node:
        print(i, ' - ', n.xpath('div/div/a')[0].get('href'))
        i += 1
    selection = input('select the manga you want to download: ')
    while not selection.isdigit() or int(selection) >= i or int(selection) <= 0:
        selection = input('please input a valid selection: ')

    title_url = 'https://mangadex.org' + node[int(selection)-1].xpath('div/div/a')[0].get('href')
    downloadTitle(title_url, session)

#downloadChapter(962609)
#downloadTitle('https://mangadex.org/title/50018/the-girl-who-is-always-smiling')
#searchTitle('one punch')

if __name__ == "__main__":
    load_dotenv()
    HEADERS = {'user-agent': os.getenv('USER_AGENT')}

    searchTitle()
