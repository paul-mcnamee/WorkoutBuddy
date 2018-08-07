import os
import re
import datetime
import BeautifulSoup
import requests
import socks
import socket
import time
import random
# creates proxy over tor identity with socks
# TODO: currently can't pull data from yelp with this enabled, might need to use their API or just not use yelp...
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9150)
socket.socket = socks.socksocket

def get_zipcodes():
    # f = open(".\US_zipcodes.txt")
    f = open(".\populated_zipcodes.txt")
    zipcodes = f.read()
    # ziplist = re.findall(r'.+(\d\d\d\d\d)', zipcodes)
    ziplist = re.findall(r'(\d\d\d\d\d)', zipcodes)
    # 43,629 zipcodes!
    # only using populated zipcodes w/ above 10k people ( around 9k zipcodes )
    f.close()
    return ziplist


def create_dir(name, zipcode):
    # get the current base file path and create a new directory
    # use the given name and date to make the new directory
    date = datetime.datetime.now().date()
    current_dir = os.path.curdir
    filename = name + "_" + zipcode + "_" + str(date)
    newdir = os.path.join(current_dir, filename)
    if os.path.exists(newdir):
        print ("Directory already exists: " + newdir)
    else:
        os.mkdir(newdir)
    return newdir



# TODO: add the correct url with the page numbers
# -- done for google, yelp, and bing
def get_url(site, page_number, zipcode):

    # Keeping this here for debugging purposes
    # zipcode = "22043"
    # problem @ 77429 on bing
    # zipcode = "77429"
    search_desc = "gym"

    # TODO: iterate through the "start=" items for yelp

    if site == 'google':
        site_url = ("https://www.google.com/search?q=" + search_desc + "+" + zipcode + "&ie=utf-8&oe=utf-8")
    elif site == 'yelp':
        site_url = ("http://www.yelp.com/search?find_desc=" + search_desc + "&find_loc=" + zipcode + "&start=0")
    elif site == 'bing':
        site_url = ("http://www.bing.com/entities/search?q=" + search_desc + "+" + zipcode + "&qpvt=" + search_desc + "+" + zipcode)
        # http://www.bing.com/entities/search?q=gym+15229&qpvt=gym+15229
        # all of the results are in the variable called pushPinData --> might be better to use this??
    elif site == 'yahoo':
        site_url = ("https://search.yahoo.com/search?p=" + search_desc + "+" + zipcode)
        # ("https://search.yahoo.com/local/s;_ylt=AwrBJR.ORKhU9CQA0CTumYlQ?p=" + search_desc + "&addr=" + zipcode)

    else:
        site_url = 'ADD URL!!'
    return site_url


def clean_results_google(site_text, zipcode, page_number):
    # make the website data clean to insert into db

    all_names = []
    all_links = []
    all_address = []

    table = site_text.find('table', {"class" : "ts"})
    if table != None:
        trs = table.findAll('tr')
        for tr in trs:
            all_links.append(tr.find('cite').text)
            all_names.append(tr.find('a').string)
            # TODO: can't find the addresses easily, just using zipcode for now... might cause duplicates
            all_address.append(zipcode)

    clean_text = [all_names, all_links, all_address]
    return clean_text


def clean_results_yelp(site_text, zipcode, page_number):
    # make the website data clean to insert into db

    all_names = []
    all_links = []
    all_address = []

    # Find the names and links for each page entry
    for name in site_text.findAll('a', { "class" : "biz-name"}):
        all_names.append(name.string)
        all_links.append(name.get('href'))
        # address = name.find('address')

    # find all of the addresses
    for address in site_text.findAll('address'):
        #TODO: Move this to the previous for loop and find the address for each name
        # maybe do this with the child relations in BeautifulSoup
        all_address.append(address.text)

    clean_text = [all_names, all_links, all_address]
    return clean_text


def clean_results_bing(site_text, zipcode, page_number):
    # make the website data clean to insert into db

    all_names = []
    all_links = []
    all_address = []

    # Find the addresses for each page entry
    for address in site_text.findAll('span', { "class" : "b_address"}):
        all_address.append(address.text)

    # Find the names and links for each page entry
    for name in site_text.findAll('h2', {"class" : "sb_h3 cttl"}):
        if name.next != "Related searches for ":
            all_names.append(name.next.text)
            all_links.append(name.next.get('href'))

    clean_text = [all_names, all_links, all_address]
    return clean_text

def clean_results_yahoo(site_text, zipcode, page_number):

    all_links = []
    all_names = []
    all_address = []

    for name in site_text.findAll('div', {"class" : "title"}):
        all_names.append(name.next.text)
        all_links.append(name.next.get('href'))

    for address in site_text.findAll('div', {"class" : "col addr"}):
        new_address = str(address)
        new_address = re.sub('<.*?>', '', new_address, 2)
        new_address = re.sub('<.*?>', u"\u0020", new_address, 2)
        new_address = re.sub('<.*?>', '', new_address, 2)
        all_address.append(new_address)
        print new_address

    clean_text = [all_names, all_links, all_address]
    return clean_text


def clean_results(site, site_text, zipcode, page_number):
    clean_text = ''
    if site == 'google':
        clean_text = clean_results_google(site_text, zipcode, page_number)
    elif site == 'yelp':
        clean_text = clean_results_yelp(site_text, zipcode, page_number)
    elif site == 'bing':
        clean_text = clean_results_bing(site_text, zipcode, page_number)
    elif site == 'yahoo':
        clean_text = clean_results_yahoo(site_text, zipcode, page_number)
    return clean_text


def main():
    sites_to_use = ['yahoo', 'bing']
    x = 1
    for zipcode in get_zipcodes():
        page_number = 1
        for site in sites_to_use:
            newdir = create_dir(site, zipcode)
            # TODO: possibly re-add the page numbers?
            # while page_number < 2:
            # create new dir for url and current datetime
            try:
                # nav to url and download site
                r = requests.get(get_url(site, page_number, zipcode))
                ufile = r.text
                # trying to use BeautifulSoup for parsing instead of REs
                site_text = BeautifulSoup.BeautifulSoup(ufile)
                # print(site_text)
                # search the downloaded file for usable data
                clean_text = clean_results(site, site_text, zipcode, page_number)
                print(clean_text)
                filename = (str(site) + "_" + str(zipcode) + "_" + str(datetime.datetime.now().date()) + ".txt")
                print (filename)
                newfile = newdir + "\\" + filename
                f = os.open(newfile, os.O_RDWR | os.O_CREAT)
                if f == '':
                    print ("File with the name of " + filename + " is empty!")
                else:
                    if clean_text != '':
                        os.write(f, str(clean_text))
                    # for entry in clean_text:
                    #     if entry != '':
                    #         os.write(f, entry. + (str(entry) + '\n'))
                os.close(f)
                # TODO: could also make the results into SQL insert statements
                # TODO: find what structure to use for the table
            except IOError:
                print('problem reading url:', get_url(site, page_number, zipcode))
                print ('Zipcode: ', zipcode)
            # page_number += 1
        # added a somewhat random sleep timer to hopefully reduce the amount of captchas or whatever
        # time.sleep(40 + random.randrange(0, 20))
        x += 1
        f = open(".\populated_zipcodes.txt", "r")
        read_zips = f.readlines()
        f.close()

        f = open(".\populated_zipcodes.txt", "w")
        for zipline in read_zips:
            if str(zipline) != str(zipcode + ' \n'):
                f.write(zipline)
        f.close()

if __name__ == '__main__':
    main()