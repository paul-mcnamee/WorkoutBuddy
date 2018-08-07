import dstk
import sqlite3
import re
import os
import os.path
import shutil
from pygeocoder import Geocoder
import ast

# The purpose of this program is to find all of the scraped text files and add them into SQL statements
#       The data needs cleaned -- there may be duplicate records
#       We need coordinates for each location
#       convert the address into a location coordinate
#       compare the coordinates
#       if there is a duplicate coordinate then add it to the final list
#       convert the text into an SQL insert statement
# TODO: add try catch and better error handling
# TODO: move files or only attempt to read the names that exist in a text file


def db_connection_create(dir):
    # connect to the database
    # pass back the connection string

    if (os.path.isfile(dir + '\locations.db')) == False:
        open(dir + '\locations.db', 'w+').close()
        con = sqlite3.connect(dir + '\locations.db')
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS locations")

        cur.execute("CREATE TABLE locations ( \
                   id INTEGER PRIMARY KEY AUTOINCREMENT,\
                   names TEXT,\
                   links TEXT,\
                   addresses TEXT,\
                   latitude REAL,\
                   longitude REAL,\
                   clean_address TEXT,\
                   bing_address INTEGER,\
                   yahoo_address INTEGER)")
        cur.execute("insert into locations values (0,'a','a','a',1,1,'a',1,1)")
        con.commit()


def db_connection():
    con = sqlite3.connect('..\locations.db')
    return con


def geocode_address(address):
    # use the address and convert it to coords
    data = dstk.DSTK({'apiBase': 'http://localhost:8080/'})
    data.api_base = 'http://localhost:8080/'
    try:
        good_address = data.street2coordinates(address)
        # usage would be good_address[address]['confidence']
        # returns the following fields in the dict:
        #       __len__         12
        #       confidence         0.878
        #       country_code         u'US'
        #       country_code3         u'USA'
        #       country_name         u'United States'
        #       fips_county         u'25015'
        #       latitude         42.37572
        #       locality         u'Amherst'
        #       longitude         -72.509542
        #       region               u'MA'
        #       street_address         u'534 Main St'
        #       street_name         u'Main St'
        #       street_number         u'534'
        if good_address[address] != None:
            return good_address
        else:
            print ("Address was not valid:" + address)
            return "INVALID_ADDRESS"
    except:
        print ("Address was not valid:" + address)
        return "INVALID_ADDRESS"


def address_is_added(address):
    # verify that the address is not added already
    # return true or false
    table_name = "locations"
    address_exists = True
    good_address = geocode_address(address)
    if good_address != str('INVALID_ADDRESS'):
        con = db_connection()
        with con:
            cur = con.cursor()
            latitude = good_address[address]['latitude']
            print latitude
            longitude = good_address[address]['longitude']
            print longitude
            sql_select = ("""select * from """ + (str(table_name)) + """ where latitude = """ + str(latitude) +
                          """ and longitude = """ + str(longitude))
            cur.execute(str(sql_select))
            results = cur.fetchall()
            count = len(results)
            if count > 0:
                address_exists = True
            else:
                address_exists = False
    return address_exists


def make_address(address):
    #       __len__         12
    #       confidence         0.878
    #       country_code         u'US'
    #       country_code3         u'USA'
    #       country_name         u'United States'
    #       fips_county         u'25015'
    #       latitude         42.37572
    #       locality         u'Amherst'
    #       longitude         -72.509542
    #       region               u'MA'
    #       street_address         u'534 Main St'
    #       street_name         u'Main St'
    #       street_number         u'534'
    country_code = str(address['country_code3'])
    zipcode = str(address['fips_county'])
    city = str(address['locality'])
    region = str(address['region'])
    street_name = str(address['street_name'])
    street_number = str(address['street_number'])
    full_address = str(street_number + " " + street_name + ", " + city + ", "
                       + region + " " + zipcode + ", " + country_code)
    return full_address


# TODO: pull some stuff out of this? It's a bit messy right now
def add_location(location, data_origin):
    # TODO: put this into a config
    table_name = "locations"
    # pull the data from the location
    new_location = ast.literal_eval(location)
    names = new_location[0]
    links = new_location[1]
    addresses = new_location[2]

    # iterate through each entry and add it to the db
    num_entries = max(len(names), len(links), len(addresses))
    i = 0

    while i < num_entries:
        if i >= len(names):
            names.append("")
        if i >= len(links):
            links.append("")
        if i >= len(addresses):
            addresses.append("")

        # check to see if the address already exists in the db
        if address_is_added(addresses[i]) != True:
            if data_origin == "bing":
                insert_origin = "1,0"
                bing_address = 1
                yahoo_address = 0
            elif data_origin == "yahoo":
                insert_origin = "0,1"
                bing_address = 0
                yahoo_address = 1
            else:
                insert_origin = "0,0"
                bing_address = 0
                yahoo_address = 0
                print ("There was no data origin for address: " + addresses[i])

            # open the db connection and insert the data
            con = db_connection()
            with con:
                c = con.cursor()
                geocoded_address = geocode_address(addresses[i])
                latitude = geocoded_address[addresses[i]]['latitude']
                longitude = geocoded_address[addresses[i]]['longitude']
                if geocoded_address != str('INVALID_ADDRESS'):
                    # only add the address if it is a good match, we don't want inaccurate data
                    if geocoded_address[addresses[i]]['confidence'] > .9:
                        c.execute("insert into " + str(table_name) + " (names, links, addresses, latitude, "
                                                                     "longitude, clean_address, bing_address, "
                                                                     "yahoo_address) values (?, ?, ?, ?, ?, ?, ?, ?)",
                            (names[i], links[i], addresses[i], latitude, longitude,
                             make_address(geocoded_address[addresses[i]]), bing_address, yahoo_address))

        # if the address is there then we still need to set the data origins
        #  and check for blank entries in names and links
        elif address_is_added(addresses[i]):
            # need to display bing or yahoo result in the db
            # later only use the addresses which have both
            con = db_connection()
            with con:
                c = con.cursor()
                geocoded_address = geocode_address(addresses[i])
                # make sure we are not adding crap addresses
                # TODO: make a function for selecting some column based on lat/long vals
                # TODO: change the updates and selects to the format with the question marks
                # TODO: for some reason it failed when updating
                if geocoded_address != str('INVALID_ADDRESS'):
                    latitude = geocoded_address[addresses[i]]['latitude']
                    longitude = geocoded_address[addresses[i]]['longitude']

                    # check if the name exists
                    name_sql = ("""select * from """ + str(table_name) + """ where latitude = """ + str(latitude) +
                                """ and longitude = """ + str(longitude) + """ and names = ''""")
                    c.execute(str(name_sql))
                    names_found = c.fetchall()
                    if len(names_found) == 0 and names[i] != "":
                        # add the name to the record
                        c.execute("update " + str(table_name) + " set names = ? where latitude = ? and longitude = ? ",
                                  (names[i], latitude, longitude))

                    # check if the link exists
                    link_sql = ("""select * from """ + str(table_name) + """ where latitude = """ + str(latitude) +
                                """ and longitude = """ + str(longitude) + """ and links = ''""")
                    c.execute(str(link_sql))
                    links_found = c.fetchall()
                    if len(links_found) == 0 and links[i] != "":
                        # add the link to the record
                        # NOTE: This should be the new way of doing it that accounts for any single or double quotes in the names.
                        c.execute("update " + str(table_name) + " set links = ? where latitude = ? and longitude = ?",
                                    (links[i], latitude, longitude))

                    sql_update = ("""update """ + str(table_name) + """ set """ + data_origin +
                                  """_address = 1 where latitude = """ + str(latitude) + """ and longitude = """ + str(longitude))
                    c.execute(str(sql_update))
        i += 1


def main():
    base_dir = os.getcwd()
    db_connection_create(base_dir + "\\Dirty")
    print (os.getcwd())
    folder_list = os.listdir(base_dir + "\\Dirty")
    # find text files in the directory
    for folder in folder_list:
        # data_origin = re.search(r'([a-zA-Z])+\_\d\d\d\d\d\_\d\d\d\d\-\d\d\-\d\d', folder)
        data_origin = re.split(r'_', folder)[0]
        if re.search(r'[a-zA-Z]+\_\d\d\d\d\d\_\d\d\d\d\-\d\d\-\d\d', folder):
            print folder
            os.chdir(base_dir + "\\Dirty\\" + folder)
            # find the text files
            text_files = os.listdir(os.path.curdir)
            for text_file in text_files:
                # open the text file
                copy_text = open(os.getcwd() + "\\" + text_file, 'r').readlines()
                for line in copy_text:
                    combined_data = open(str(base_dir) + "\\combined_data.txt", 'a')
                    combined_data.write("\n" + str(line))
                    combined_data.close()
                    add_location(line, data_origin)
                # text_file.close()
        os.chdir(base_dir)
        if folder != 'locations.db':
            shutil.move((base_dir + "\\Dirty\\" + folder), (base_dir + "\\Complete"))

if __name__ == '__main__':
    main()