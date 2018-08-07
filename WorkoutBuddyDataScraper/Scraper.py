__author__ = 'paulm_000'
import time
import shutil
import os
import re
import sys
import datetime
import urllib

import scrapy


def create_dir(name, zipcode):
    # get the current base file path and create a new directory
    # use the given name and date to make the new directory
    # TODO: check to see if the directory is there before creating it
    date = datetime.datetime
    dir = os.path.dirname()
    filename = name + "_" + zipcode + "_" + date
    newdir = os.path.join(dir, filename)
    os.mkdir(newdir)


# TODO: add the correct url with the page numbers
# TODO: add zip code list and iterate through each one
def get_url(site, page_number, zipcode):
    if site == 'google':
        site_url = 'http://google.com'
    elif site == 'yelp':
        site_url = 'http://yelp.com'
    elif site == 'bing':
        site_url = ("www.bing.com/search?q=restaurants+" + zipcode + "22180&qs=n&form=QBLH&pq"
                     "=restaurants+" + zipcode + "22180&sc=4-17&sp=-1&sk=&cvid=86776aaf961f42faa11e0a7dd14e43a1")
    else:
        site_url = 'ADD URL!!'
    return site_url


# TODO: look at each site and write the methods of cleaning the data
def clean_results_google(site_text):
    # make the website data clean to insert into db
    clean_text = ''
    return clean_text


def clean_results_yelp(site_text):
    # make the website data clean to insert into db
    clean_text = ''
    return clean_text


def clean_results_bing(site_text):
    # make the website data clean to insert into db
    f = site_text
    text = f.read()
    tuples = re.findall(r'', text)
    # TODO: read the tuples, and add the zipcode to each tuple
    # TODO: figure out which data is necessary
    clean_text = ''
    return clean_text


def clean_results(site, site_text):
    clean_text = ''
    if site == 'google':
        clean_text = clean_results_google(site_text)
    elif site == 'yelp':
        clean_text = clean_results_yelp(site_text)
    elif site == 'bing':
        clean_text = clean_results_bing(site_text)
    return clean_text


def main():
    sites_to_use = ['google', 'yelp', 'bing']
    x = 1

    while x < 99999:
        zipcode = "%05d" % x
        page_number = 1

        for site in sites_to_use:
            create_dir(site, zipcode)
            #while page_number < 3:
            # create new dir for url and current datetime
            try:
                # nav to url and download site
                ufile = urllib.urlopen(get_url(site, page_number, zipcode))
                if ufile.info().gettype() == 'text/html':
                    site_text = ufile.read()
                    # search the downloaded file for usable data
                    clean_text = clean_results(site, site_text)
                    # TODO: need to write to a csv or something to bulk add to db
                    # TODO: search the directory (2 levels up) for the file name



                    # TODO: could also make the results into SQL insert statements
                    # TODO: find what structure to use for the table
            except IOError:
                print('problem reading url:', get_url(site, page_number, zipcode))
            #page_number += 1
            time.sleep(5)
    x += 1

if __name__ == '__main__':
    main()
