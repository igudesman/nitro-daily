# Create your tasks here

from __future__ import absolute_import, unicode_literals
from celery import shared_task

from celery.task import periodic_task
from celery.schedules import crontab

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

import os
from time import sleep
import csv
import pandas as pd

from scraping.models import Player
from scraping.models import Prediction
from scraping.models import Opta
from scraping.models import Sport

import datetime

import gc


READY = False
#################################################################################

def find_player(driver, name):
    search_button = driver.find_element_by_xpath('/html/body/nav/div[1]/div/div/div[3]/div/button').click()

    search = driver.find_element_by_xpath('/html/body/nav/div[1]/div/div/div[3]/div/div/form/input')
    search.send_keys(name)
    try:
        stat_link = driver.find_element_by_xpath('/html/body/nav/div[1]/div/div/div[3]/div/div/ul/li[1]/a').get_attribute('href') + 'stat/'
    except:
        print('No player stats')
        return False
    
    driver.get(stat_link)
    
    try:
        error = driver.find_element_by_xpath('//*[@id="branding-layout"]/div[2]/div[3]/div')
        return False
    except:
        pass
        
    return True


def sport(driver):

    # df_predictions = pd.read_csv('predictions.csv')
    # df_opta = pd.read_csv('opta.csv')
    # diff_names = pd.concat([df_predictions['Name'], df_opta['Name']]).drop_duplicates().reset_index(drop=True)

    prediction_names = []
    for pred in Prediction.objects.all():
        prediction_names.append(pred.name)
    
    opta_names = []
    for o in Opta.objects.all():
        opta_names.append(o.name)

    diff_names = prediction_names + list(set(opta_names) - set(prediction_names))


    driver.get('https://www.sports.ru/')
    for i, name in enumerate(diff_names):
        
        is_already_present = False
        current_database_entry = None

        for player in Sport.objects.all():
            if player.name == name:
                current_database_entry = player
                is_already_present = True
                break


        found = False
        while True:
            try: 
                if find_player(driver, name) == False:
                    print('Did not find: ', name)
                    break

                found = True
                break
            except:
                print('Problem with searching..')
                driver.get('https://www.sports.ru/')
                sleep(10)

        if not found:
            continue
        
        total_matches = 0
        ok = True
        current_option = 1

        count_needed_matches = 0
        count_match_sixty = 0
        count_match_ninety = 0
        
        total_minn = 0
        total_goly = 0
        total_pen = 0
        total_pas = 0
        total_zhelt = 0
        total_kras = 0


        while ok:

            try:
                driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[1]/div[2]/select/option[{current_option}]'.format(current_option=current_option)).click()
            except:
                ok = False
                break
            
            entry = 1
            while True:
                
                try:
                    driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]'.format(entry=entry))
                except:
                    break
                
                try:
                    start = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[6]'.format(entry=entry)).text)
                    end = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[7]'.format(entry=entry)).text)
                    minn = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[8]'.format(entry=entry)).text)
                    goly = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[9]'.format(entry=entry)).text)
                    pen = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[10]'.format(entry=entry)).text)
                    pas = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[11]'.format(entry=entry)).text)
                    zhelt = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[13]'.format(entry=entry)).text)
                    kras = int(driver.find_element_by_xpath('//*[@id="branding-layout"]/div/div[2]/div[2]/div[2]/div/div[2]/table/tbody/tr[{entry}]/td[14]'.format(entry=entry)).text)
                except:
                    total_matches += 1
                    entry += 1
                    continue
                    
                if start == 1:
                    count_needed_matches += 1
                    if minn >= 60:
                        count_match_sixty += 1
                    if minn >= 90:
                        count_match_ninety += 1
                
                total_minn += minn
                total_goly += goly
                total_pen += pen
                total_pas += pas
                total_zhelt += zhelt
                total_kras += kras
                
                entry += 1
                total_matches += 1
                
                if total_matches >= 100:
                    ok = False
                    break
                
            current_option += 1
            
        if count_needed_matches != 0:
            sixty = float(count_match_sixty) / count_needed_matches
            ninety = float(count_match_ninety) / count_needed_matches
        else:
            sixty = 0
            ninety = 0
        
        if total_minn != 0:
            yel = (float(total_zhelt)/total_minn) * 90
            red = (float(total_kras)/total_minn) * 90
        
        print('All ok: ', name)
        if is_already_present:
            current_database_entry.name = name
            current_database_entry.sixty = sixty
            current_database_entry.ninety = ninety
            current_database_entry.total_goals = total_goly
            current_database_entry.total_pen = total_pen
            current_database_entry.total_pas = total_pas
            current_database_entry.total_yellow = yel
            current_database_entry.total_red = red
            current_database_entry.date = datetime.datetime.now()
            current_database_entry.save()
        else:
            new_player = Sport(name=name, sixty=sixty, ninety=ninety, total_goals=total_goly, total_pen=total_pen, total_pas=total_pas, total_yellow=yel, total_red=red, date=datetime.datetime.now())
            new_player.save()

        # df = df.append({'Name': name, '60 min': sixty, '90 min': ninety, 'Total goals': total_goly, 'Total pen': total_pen, 'Total pas': total_pas, 'Yellow cards': yel, 'Red cards': red}, ignore_index=True)
        # df.to_csv('sports.csv', index=False)

#########################################################################################


def login(driver):
    driver.get('https://fantasyfootballhub.co.uk/predictions/')
    driver.find_element_by_xpath('//*[@id="menu-item-11272"]/a').click()

    login = driver.find_element_by_xpath('//*[@id="user_login"]')
    login.send_keys('sazam')

    password = driver.find_element_by_xpath('//*[@id="user_pass"]')
    password.send_keys('fantasyfootball')

    driver.find_element_by_xpath('//*[@id="wp-submit"]').click()

    global READY
    READY = True


def load_more(driver):
    
    # driver.execute_script("window.scrollTo(0, 3000)")
    sleep(1)
    load_button = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[4]/button')

    end = driver.find_element_by_xpath('//*[@id="post-23243"]/div[3]')
    actions = ActionChains(driver)
    actions.move_to_element(end).perform()

    load_button.click()
    print('LOAD..')


def get_all_players_prediction(driver):

    while True:
        try:
            login(driver)
            break
        except:
            pass

    driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[1]/div[3]/div[2]/div[2]').click()
    move = ActionChains(driver)
    thumb = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[1]/div[3]/div[3]/div[2]/ng5-slider/span[6]')
    thumb.click()
    move.click_and_hold(thumb).move_by_offset(100, 0).release().perform()
    sleep(3)

    div_index = 1
    ok = True
    already_loaded = False
    page = 1
    count = 0
    second_chance = True

    while ok:
        try:
            if page == 1:
                player_name = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[2]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-title'.format(div_index=div_index))
            else:
                player_name = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[3]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-title'.format(div_index=div_index))
            already_loaded = False
        except:
            if not already_loaded:
                try:
                    load_more(driver)
                    page += 1
                    if page == 2:
                        div_index = 1
                except:
                    print('No more pages')
                    print(div_index)
                    break
                already_loaded = True
            else:                                   
                break
        try:
            if page == 1:
                player_name = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[2]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-title'.format(div_index=div_index)).text
                team = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[2]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-subtitle'.format(div_index=div_index)).text
                role = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[2]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-subtitle'.format(div_index=div_index)).text.split(' ')[1]
                goal = float(driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[2]/div[{div_index}]/mat-card/div[2]/div[2]/div[1]/div/div[1]/div[2]/span'.format(div_index=div_index)).text)
                assist = float(driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[2]/div[{div_index}]/mat-card/div[2]/div[2]/div[1]/div/div[2]/div[2]/span'.format(div_index=div_index)).text)
                cs = float(driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[2]/div[{div_index}]/mat-card/div[2]/div[2]/div[1]/div/div[3]/div[2]/span'.format(div_index=div_index)).text)
            else:
                player_name = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[3]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-title'.format(div_index=div_index)).text
                team = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[3]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-subtitle'.format(div_index=div_index)).text
                role = driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[3]/div[{div_index}]/mat-card/div[1]/mat-card-header/div[2]/mat-card-subtitle'.format(div_index=div_index)).text.split(' ')[1]
                goal = float(driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[3]/div[{div_index}]/mat-card/div[2]/div[2]/div[1]/div/div[1]/div[2]/span'.format(div_index=div_index)).text)
                assist = float(driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[3]/div[{div_index}]/mat-card/div[2]/div[2]/div[1]/div/div[2]/div[2]/span'.format(div_index=div_index)).text)
                cs = float(driver.find_element_by_xpath('//*[@id="post-23243"]/div[2]/div/app-root/div/app-predictions/div[3]/div[{div_index}]/mat-card/div[2]/div[2]/div[1]/div/div[3]/div[2]/span'.format(div_index=div_index)).text)
        except:
            if second_chance:
                second_chance = False
                continue
            else:
                div_index += 1
                second_chance = True

        spaces = 0
        for i, symbol in enumerate(team):
            if spaces == 2:
                team = team[i::]
                break

            if symbol == ' ':
                spaces += 1

        is_already_present = False
        current_database_entry = None

        for player in Prediction.objects.all():
            if player.name == player_name:
                current_database_entry = player
                is_already_present = True
                break

        if is_already_present:
            current_database_entry.name = player_name
            current_database_entry.team = team
            current_database_entry.role = role
            current_database_entry.goal = goal
            current_database_entry.assist = assist
            current_database_entry.cs = cs
            current_database_entry.date = datetime.datetime.now()
            current_database_entry.save()
        else:
            new_player = Prediction(name=player_name, team=team, role=role, goal=goal, assist=assist, cs=cs, date=datetime.datetime.now())
            new_player.save()

        # df = df.append({'Name': player_name, 'Team': team, 'Role': role, 'Goal': goal, 'Assist': assist, 'Cs': cs}, ignore_index=True)
        # df.to_csv('predictions.csv', index=False)
        print('{0}. Name: {1}; Team: {2}; Role: {3}'.format(count, player_name, team, role))
        div_index += 1
        count += 1
        second_chance = True

################################################################



def get_all_players_opta(driver):

    if not READY:
        login(driver)

    driver.get('https://fantasyfootballhub.co.uk/opta/')

    custom = driver.find_element_by_xpath('//*[@id="mat-input-3"]/option[14]').click()

    move = ActionChains(driver)
    thumb = driver.find_element_by_xpath('//*[@id="post-12098"]/div[2]/div/app-root/div/div/div[2]/div[2]/div[2]/ng5-slider/span[5]')
    thumb.click()
    move.click_and_hold(thumb).move_by_offset(-700, 0).release().perform()
    
    end = driver.find_element_by_xpath('//*[@id="post-12098"]/div[3]')
    move.move_to_element(end).perform()
    
    all = driver.find_element_by_xpath('//*[@id="mat-input-4"]/option[5]').click()
    sleep(2)
    
    while True:
        try:
            loading = driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/div/div/div')
        except:
            break

    print('READY!')

    entry_index = 1
    while True:
        try:
            name = driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/table/tbody/tr[{entry_index}]/td[1]/span[2]'.format(entry_index=entry_index))
        except:
            print(entry_index)
            break
        
        name = name.text.split(' (')[0]
        team = driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/table/tbody/tr[{entry_index}]/td[1]/span[4]'.format(entry_index=entry_index)).text
        bc = float(driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/table/tbody/tr[{entry_index}]/td[4]'.format(entry_index=entry_index)).text)
        npxg = float(driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/table/tbody/tr[{entry_index}]/td[5]'.format(entry_index=entry_index)).text)
        xg = float(driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/table/tbody/tr[{entry_index}]/td[6]'.format(entry_index=entry_index)).text)
        bcc = float(driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/table/tbody/tr[{entry_index}]/td[10]'.format(entry_index=entry_index)).text)
        xa = float(driver.find_element_by_xpath('//*[@id="mat-tab-content-0-0"]/div/div/table/tbody/tr[{entry_index}]/td[11]'.format(entry_index=entry_index)).text)
        
        is_already_present = False
        current_database_entry = None

        for player in Opta.objects.all():
            if player.name == name:
                current_database_entry = player
                is_already_present = True
                break

        if is_already_present:
            current_database_entry.name = name
            current_database_entry.team = team
            current_database_entry.bc = bc
            current_database_entry.npxg = npxg
            current_database_entry.xg = xg
            current_database_entry.bcc = bcc
            current_database_entry.xa = xa
            current_database_entry.date = datetime.datetime.now()
            current_database_entry.save()
        else:
            new_player = Opta(name=name, team=team, bc=bc, npxg=npxg, xg=xg, bcc=bcc, xa=xa, date=datetime.datetime.now())
            new_player.save()

        # df = df.append({'Name': name, 'Team': team, 'BC': bc, 'NPxG': npxg, 'xG': xg, 'BCC': bcc, 'xA': xa}, ignore_index=True)
        # df.to_csv('opta.csv', index=False)
        print({'Name': name, 'Team': team, 'BC': bc, 'NPxG': npxg, 'xG': xg, 'BCC': bcc, 'xA': xa})
        entry_index += 1

        gc.collect()
        
    print('Done!')

#############################

@shared_task
def update_data():

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    prefs = {"download.default_directory" : os.getcwd()}
    chrome_options.add_experimental_option("prefs",prefs)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    driver.maximize_window()
    driver.implicitly_wait(10)

    # columns = ['Name', '60 min', '90 min', 'Total goals', 'Total pen', 'Total pas', 'Yellow cards', 'Red cards']
    # df = pd.DataFrame(columns=columns)

    # get_all_players_prediction(driver)
    # get_all_players_opta(driver)
    sport(driver)


def get_players(driver):

    size = driver.get_window_size()
    print("Window size: width = {}px, height = {}px".format(size["width"], size["height"]))
    sleep(5)
    driver.execute_script("window.scrollTo(0, 500)") 
    sleep(3)
    actions = ActionChains(driver)
    actions.move_by_offset(350, 700).click().perform()
    sleep(5)

@shared_task
def my_first_task(names):
    
    Player.objects.all().delete()
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    # prefs = {"download.default_directory" : os.getcwd()}
    # chrome_options.add_experimental_option("prefs",prefs)
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument('window-size=1920x1080')
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--proxy-server='direct://'")
    # chrome_options.add_argument("--proxy-bypass-list=*")
    # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # driver.maximize_window()
    # driver.implicitly_wait(10)

    # TRIES = 5
    # driver.get(url)
    # limit = len([f for f in os.listdir('.') if f.endswith('.csv')])

    # while TRIES > 0:
    #     try:
    #         get_players(driver)
    #     except:
    #         driver.close()
    #         my_first_task(url)
    #         return None
    #     sleep(3)
    #     csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    #     print(csv_files)
    #     if len(csv_files) <= limit:
    #         driver.refresh()
    #         TRIES -= 1
    #         continue
    #     else:
    #         break
            
    # if TRIES <= 0:
    #     raise ValueError('should be only one txt file in the current directory')

    # for csv_file in csv_files:
    #     if csv_file != 'player_stats.csv':
    #         filename = csv_file
    #         break

    print('1')
    players = pd.read_csv('player_stats.csv')
    allData = []
    print('2')
    players.fillna(0, inplace=True)
    print('3')

    for i, name in enumerate(players['name']):
        for also_name in names:
            if also_name in name:
                krik = players.loc[i]
                allData.append(dict(krik))
                print(name)
                break

    for i in range(len(allData)):
        temp = Player(**(allData[i]))
        temp.save()
        print('Saved')
    # get_player_stats(driver, temp)

    # os.remove(filename)