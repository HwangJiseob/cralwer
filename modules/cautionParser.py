import json, time, requests, re, os, csv, signal, traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def create_caution_standard(soup):
    form = soup.find_all('form')[1]

    standard = {}
    i = 0
    for tr in form.find_all('tr')[1].find_all('tr'):
        if i < 2:
            pass
        else:
            td = tr.find_all('td')
            code = td[2].text
            descrption = td[3] 

            standard[code] = descrption.text
        i += 1
    
    standard['폐강'] = '폐강'
    return standard

def parse_cautions(driver, lect, caution_path, input_ocode1, input_ohakkwa, standard, row_idx):

    # row_idx는 초기값이 0기준이 아니라 1기준이어서 1을 빼주어야 한다.
    caution_idx = row_idx - 1


    cautions_exist = True
    caution_arr = []
    try:
        caution_sel = "#row"+ str(caution_idx) +"jqxgrid > " + caution_path
        WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, caution_sel)))
        caution_text = lect.find_element_by_css_selector(caution_path).text
        # 만약 여기서 폐강 뜨면 수집 시간이 10초나 걸림.
    except:
        try:
            caution_sel = "#row"+ str(caution_idx) +"jqxgrid > div:nth-child(17) > span > font"
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, caution_sel)))
            caution_text = lect.find_element_by_css_selector("div:nth-child(17) > span > font").text
        except:
            cautions_exist = False
            
    if cautions_exist:
        for key in standard:
            resultType = re.search(key, caution_text)
            if resultType == None:
                pass
            else:
                caution_arr.append(standard[key])
        # return {input_ocode1: {input_ohakkwa: caution_arr}}
        return caution_arr
    else:
        return caution_arr

