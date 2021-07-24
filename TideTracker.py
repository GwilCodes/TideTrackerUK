'''
****************************************************************
****************************************************************

                TideTracker for E-Ink Display

                        by Sam Baker
        Modified for UK tides API and 5.83" screen by Gwil

****************************************************************
****************************************************************
'''

import config
import sys
import os
import time
import traceback
import requests, json
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import http.client, urllib.request, urllib.parse, urllib.error, base64, json
import pandas as pd
import pytz

sys.path.append('lib')
from lib.waveshare_epd import epd5in83_V2
from PIL import Image, ImageDraw, ImageFont

picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
icondir = os.path.join(picdir, 'icon')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')

'''
****************************************************************

Location specific info required

****************************************************************
'''

# Optional, displayed on top left
LOCATION = config.location

# For weather data
# Create Account on openweathermap.com and get API key
API_KEY = config.weather_api_key

# Create Account on admiralty.co.uk and get API key
TIDE_API_KEY = config.tide_api_key

# Admiralty tides API station ID
TIDE_STATION = config.tide_station

# Get LATITUDE and LONGITUDE of location
LATITUDE = config.latitude
LONGITUDE = config.longitude
UNITS = config.units

# Create URL for API call
BASE_URL = 'http://api.openweathermap.org/data/2.5/onecall?'
URL = BASE_URL + 'lat=' + LATITUDE + '&lon=' + LONGITUDE + '&units=' + UNITS +'&appid=' + API_KEY


'''
****************************************************************

Functions and defined variables

****************************************************************
'''

# define funciton for writing image and sleeping for specified time
def write_to_screen(image, sleep_seconds):
    print('Writing to screen.') # for debugging
    # Create new blank image template matching screen resolution
    h_image = Image.new('1', (epd.width, epd.height), 255)
    # Open the template
    screen_output_file = Image.open(os.path.join(picdir, image))
    # Initialize the drawing context with template as background
    h_image.paste(screen_output_file, (0, 0))
    epd.display(epd.getbuffer(h_image))
    # Sleep
    epd.sleep() # Put screen to sleep to prevent damage
    print('Sleeping for ' + str(sleep_seconds) +'.')
    time.sleep(sleep_seconds) # Determines refresh rate on data
    epd.init() # Re-Initialize screen


# define function for displaying error
def display_error(error_source):
    # Display an error
    print('Error in the', error_source, 'request.')
    # Initialize drawing
    error_image = Image.new('1', (epd.width, epd.height), 255)
    # Initialize the drawing
    draw = ImageDraw.Draw(error_image)
    draw.text((100, 150), error_source +' ERROR', font=font50, fill=black)
    draw.text((100, 300), 'Retrying in 30 seconds', font=font22, fill=black)
    current_time = datetime.now().strftime('%H:%M')
    draw.text((100, 365), 'Last Refresh: ' + str(current_time), font = font50, fill=black)
    # Save the error image
    error_image_file = 'error.png'
    error_image.save(os.path.join(picdir, error_image_file))
    # Close error image
    error_image.close()
    # Write error to screen
    write_to_screen(error_image_file, 30)


# define function for getting weather data
def getWeather(URL):
    # Ensure there are no errors with connection
    error_connect = True
    while error_connect == True:
        try:
            # HTTP request
            print('Attempting to connect to OWM.')
            response = requests.get(URL)
            print('Connection to OWM successful.')
            error_connect = None
        except:
            # Call function to display connection error
            print('Connection error.')
            display_error('CONNECTION')

    # Check status of code request
    if response.status_code == 200:
        print('Connection to Open Weather successful.')
        # get data in jason format
        data = response.json()

        with open('data.txt', 'w') as outfile:
            json.dump(data, outfile)

        return data

    else:
        # Call function to display HTTP error
        display_error('HTTP')

# Get UK tide data
def ukTide():
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': TIDE_API_KEY,
    }

    params = urllib.parse.urlencode({
        # Request parameters - number of days of records
        'duration': '5',
    })

    try:
        conn = http.client.HTTPSConnection('admiraltyapi.azure-api.net')
        conn.request("GET", "/uktidalapi/api/V1/Stations/"+ TIDE_STATION + "/TidalEvents?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        #print(data)
        decoded = json.loads(data.decode('UTF-8'))
        print('Tide data successful')
        conn.close()
        global ukTides
        ukTides = decoded
        return decoded
    except Exception as e:
        display_error('HTTP')
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# Adjust times from UTC to current local time
def utc_to_local(utc_dt):
        local_tz = pytz.timezone("Europe/London")
        return utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)

# Plot last 24 hours of tide
def plotTide(TideData):
    TideData['Date'] = pd.to_datetime(TideData['Date'])
    tide_time = TideData['Date'].dt.strftime("%a")

    # Create Plot
    fig, axs = plt.subplots(figsize=(10, 4))
    fig.subplots_adjust(bottom=0.2)
    TideData['Height'].plot.bar(ax=axs, color='black')
    axs.set_xticklabels(tide_time)
    plt.title('Tide - Next 4 Days', fontsize=20)
    #fontweight="bold",
    #axs.xaxis.set_tick_params(labelsize=20)
    #axs.yaxis.set_tick_params(labelsize=20)
    plt.savefig('images/TideLevel.png', dpi=60)
    #plt.show()

# Set the font sizes
font15 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 15)
font20 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 20)
font22 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 22)
font30 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 30)
font35 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 35)
font50 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 50)
font60 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 60)
font100 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 100)
font160 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 160)

# Set the colors
black = 'rgb(0,0,0)'
white = 'rgb(255,255,255)'
grey = 'rgb(235,235,235)'


'''
****************************************************************

Main Loop

****************************************************************
'''

# Initialize and clear screen
print('Initializing and clearing screen.')
epd = epd5in83_V2.EPD() # Create object for display functions
epd.init()
epd.Clear()

ukTides = ''

while True:
    # Get weather data
    data = getWeather(URL)
    # get current dict block
    current = data['current']
    # get current
    temp_current = current['temp']
    # get feels like
    feels_like = current['feels_like']
    # get humidity
    humidity = current['humidity']
    # get pressure
    wind = current['wind_speed']
    # get description
    weather = current['weather']
    report = weather[0]['description']
    # get icon url
    icon_code = weather[0]['icon']

    # get daily dict block
    daily = data['daily']
    # get daily precip
    daily_precip_float = daily[0]['pop']
    #format daily precip
    daily_precip_percent = daily_precip_float * 100
    # get min and max temp
    daily_temp = daily[0]['temp']
    temp_max = daily_temp['max']
    temp_min = daily_temp['min']

    # Set strings to be printed to screen
    string_location = LOCATION
    string_temp_current = format(temp_current, '.0f') + u'\N{DEGREE SIGN}C'
    string_feels_like = 'Feels like: ' + format(feels_like, '.0f') +  u'\N{DEGREE SIGN}C'
    string_humidity = 'Humidity: ' + str(humidity) + '%'
    string_wind = 'Wind: ' + format(wind, '.1f') + ' MPH'
    string_report = 'Now: ' + report.title()
    string_temp_max = 'High: ' + format(temp_max, '>.0f') + u'\N{DEGREE SIGN}C'
    string_temp_min = 'Low:  ' + format(temp_min, '>.0f') + u'\N{DEGREE SIGN}C'
    string_precip_percent = 'Precip: ' + str(format(daily_precip_percent, '.0f'))  + '%'

    # get min and max temp
    nx_daily_temp = daily[1]['temp']
    nx_temp_max = nx_daily_temp['max']
    nx_temp_min = nx_daily_temp['min']
    # get daily precip
    nx_daily_precip_float = daily[1]['pop']
    #format daily precip
    nx_daily_precip_percent = nx_daily_precip_float * 100

    # get min and max temp
    nx_nx_daily_temp = daily[2]['temp']
    nx_nx_temp_max = nx_nx_daily_temp['max']
    nx_nx_temp_min = nx_nx_daily_temp['min']
    # get daily precip
    nx_nx_daily_precip_float = daily[2]['pop']
    #format daily precip
    nx_nx_daily_precip_percent = nx_nx_daily_precip_float * 100

    # Tomorrow Forcast Strings
    nx_day_high = 'High: ' + format(nx_temp_max, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_day_low = 'Low: ' + format(nx_temp_min, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_precip_percent = 'Precip: ' + str(format(nx_daily_precip_percent, '.0f'))  + '%'
    nx_weather_icon = daily[1]['weather']
    nx_icon = nx_weather_icon[0]['icon']

    # Overmorrow Forcast Strings
    nx_nx_day_high = 'High: ' + format(nx_nx_temp_max, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_nx_day_low = 'Low: ' + format(nx_nx_temp_min, '>.0f') + u'\N{DEGREE SIGN}C'
    nx_nx_precip_percent = 'Precip: ' + str(format(nx_nx_daily_precip_percent, '.0f'))  + '%'
    nx_nx_weather_icon = daily[2]['weather']
    nx_nx_icon = nx_nx_weather_icon[0]['icon']

    # Last updated time
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    last_update_string = 'Last Updated: ' + current_time

    # Current Date
    current_date = now.strftime("%A, %d %B %Y")

    # Tide Data
    # Get water level
    wl_error = True
    while wl_error == True:
        try:
            WaterLevel = ukTide()

            wl_error = False
        except:
            display_error('Tide Data')

    WaterFormatted = pd.DataFrame(WaterLevel)
    # print(WaterFormatted)
    plotTide(WaterFormatted)


    # Open template file
    template = Image.open(os.path.join(picdir, 'template.png'))
    # Initialize the drawing context with template as background
    draw = ImageDraw.Draw(template)

    # Current weather
    ## Open icon file
    icon_file = icon_code + '.png'
    icon_image = Image.open(os.path.join(icondir, icon_file))
    icon_image = icon_image.resize((130,130))
    template.paste(icon_image, (30, 70))

    lw, lh = draw.textsize(LOCATION, font=font35)
    lcenter = int((310-lw)/2,)

    draw.text((lcenter,10), LOCATION, font=font35, fill=black)
    dw, dh = draw.textsize(current_date, font=font20)
    dcenter = int((310-dw)/2,)

    draw.text((dcenter,50), current_date, font=font20, fill=black)
    
    # Center current weather report
    w, h = draw.textsize(string_report, font=font20)
    # print(w)
    if w > 180:
        string_report = 'Now:\n' + report.title()
    w, h = draw.textsize(string_report, font=font20)
    
    center = int((200-w)/2,)
    
    draw.text((center,185), string_report, font=font20, fill=black)

    # Data
    draw.text((200,75), string_temp_current, font=font35, fill=black)
    y = 120
    draw.text((200,y), string_feels_like, font=font15, fill=black)
    draw.text((200,y+20), string_wind, font=font15, fill=black)
    draw.text((200,y+40), string_precip_percent, font=font15, fill=black)
    draw.text((200,y+60), string_temp_max, font=font15, fill=black)
    draw.text((200,y+80), string_temp_min, font=font15, fill=black)

    # Weather Forcast
    # Tomorrow
    icon_file = nx_icon + '.png'
    icon_image = Image.open(os.path.join(icondir, icon_file))
    icon_image = icon_image.resize((130,130))
    template.paste(icon_image, (330, 50))
    draw.text((340,20), 'Tomorrow', font=font22, fill=black)
    draw.text((320,180), nx_day_high, font=font15, fill=black)
    draw.text((400,180), nx_day_low, font=font15, fill=black)
    draw.text((355,200), nx_precip_percent, font=font15, fill=black)

    # Next Next Day Forcast
    icon_file = nx_nx_icon + '.png'
    icon_image = Image.open(os.path.join(icondir, icon_file))
    icon_image = icon_image.resize((130,130))
    template.paste(icon_image, (495, 50))
    draw.text((520,20), 'Day After', font=font22, fill=black)
    draw.text((490,180), nx_nx_day_high, font=font15, fill=black)
    draw.text((570,180), nx_nx_day_low, font=font15, fill=black)
    draw.text((525,200), nx_nx_precip_percent, font=font15, fill=black)


    ## Dividing lines
    draw.line((310,10,310,220), fill='black', width=3)
    draw.line((480,20,480,210), fill='black', width=2)


    # Tide Info
    # Graph
    tidegraph = Image.open('images/TideLevel.png')
    template.paste(tidegraph, (95, 245))

    # Large horizontal dividing line
    h = 240
    draw.line((25, h, 625, h), fill='black', width=3)

    # Daily tide times
    draw.text((20,260), "Today's Tide", font=font22, fill=black)

    # Get tide time predictions
    hilo_error = True
    while hilo_error == True:
        try:
            ukTideData = ukTides
            hilo_error = False
        except:
            display_error('Tide Prediction')

    # Display tide preditions
    y_loc = 300 # starting location of list
    # Iterate over preditions
    
    hilo_daily = pd.DataFrame(ukTideData)

    # Limit tides to next 4 records
    for i, row in hilo_daily.iloc[:4].iterrows():
        # For high tide
        if row['EventType'] == 'HighWater':
            strippedTime = row['DateTime'].split('.', 1)[0]
            correct_time = utc_to_local(datetime.fromisoformat(strippedTime))
            tide_time = correct_time.strftime("%H:%M")
            tidestr = "High: " + tide_time
        # For low tide
        elif row['EventType'] == 'LowWater':
            strippedTime = row['DateTime'].split('.', 1)[0]
            correct_time = utc_to_local(datetime.fromisoformat(strippedTime))
            tide_time = correct_time.strftime("%H:%M")
            tidestr = "Low:  " + tide_time

        # Draw to display image
        draw.text((40,y_loc), tidestr, font=font15, fill=black)
        y_loc += 25 # This bumps the next prediction down a line

    draw.text((20,445), last_update_string, font=font15, fill=black)

    # Save the image for display as PNG
    screen_output_file = os.path.join(picdir, 'screen_output.png')
    template.save(screen_output_file)
    # Close the template file
    template.close()

    write_to_screen(screen_output_file, 600)
    #epd.Clear()
