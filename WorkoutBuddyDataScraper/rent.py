# Kyle's Rent

from __future__ import division

apartment_sqft = 880
apartment_rent = 1250
cable_bill = 150
electricity = 60
netflix = 16
food = 10
days_lived = 3.5 * 4

percent_time_lived = float(3.5 / 7)

def new_payment(payment):
    new = ((payment * percent_time_lived) / 3)
    return new

occupied_sqft = .60 * apartment_sqft
new_rent = apartment_rent * (occupied_sqft / apartment_sqft) * percent_time_lived
new_cable_bill = new_payment(cable_bill)
new_electricity = new_payment(electricity)

total_rent = new_rent + new_cable_bill + new_electricity + food + (netflix / 4)
print (" Monthly Rent = " + str(total_rent))
daily_rent = total_rent / days_lived
print ("Daily Rent = " + str(daily_rent))