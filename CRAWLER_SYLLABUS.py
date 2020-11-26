from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


from bs4 import BeautifulSoup
import json, time, requests, re, os, csv, signal, random

from modules.dataIterator import *
from modules.resultParser import *
from modules.logger import *
from modules.cautionParser import *

# logger 실행
LOG = StandardLogger().get_logger()


while True:
    input_target_semester = input('TARGET_SEMESTER(ex 20202): ')
    if (len(input_target_semester) == 5 and input_target_semester.isdecimal()
        and input_target_semester[-1] in ['1', '2', '3', '4']
        and int(input_target_semester[:4]) > 2015):
        TARGET_SEMESTER = input_target_semester
        break
    else:
        print("잘못된 학기 데이터입니다.")



TARGET_YEAR = TARGET_SEMESTER[:4]
TARGET_HG   = TARGET_SEMESTER[-1]


# CATEGORIES 정리
MAJORS      = ["문과대학", "상경대학", "경영대학", "이과대학", "공과대학", "생명시스템대학",
               "신과대학", "사회과학대학", "음악대학", "생활과학대학", "교육과학대학",
               "언더우드국제대학", "글로벌인재대학"]
MEDICALS    = ["약학대학", "의과대학", "치과대학", "간호대학"]
SPECIALS    = ["연계전공", "ROTC", "Study Abroad Course", "교직과정", "국내교환대학", "공통"]
ELECTIVES   = ["교양기초(2019학번~)", "대학교양(2019학번~)", "기초교육(2019학번~)", "국제캠퍼스(2019학번~)",
               "공통기초(10~18학번)", "필수교양(10~18학번)", "선택교양(10~18학번)", "(~2018학번)국제캠퍼스"]
ALL = MAJORS + MEDICALS + SPECIALS + ELECTIVES
SEARCH      = []    # 수기 입력
CATEGOIRES  = ['MAJORS', 'MEDICALS', 'SPECIALS', 'ELECTIVES', 'ALL', 'SEARCH']



# 주요 element들의 selector 목록
selector = {
    "HY"    :"#HY",             # 연도
    "HG"    :"#HG",             # 학기
    "OCODE0":"#OCODE0",         # 학부
    "OCODE1":"#OCODE1",         # 단과대학 및 교양 대분류
    "S2"    :"#S2",             # 학과 및 교양 소분류
    "search_btn"    : 'a[href="javascript:searchGb(\'search\',1);"]',
    "next_page_btn" : '#pager > div > div > div:nth-child(2)',
    "page_info"     : '#pager > div > div > div:nth-child(3)',
    "lect_list"     : '#contenttablejqxgrid > div[role="row"]',
    "caution_path"  : 'div:nth-child(17) > span > a',
    "No data"       : "#row0jqxgrid > div:nth-child(5) > span"
}


# selenium & requests 관련 전역변수



BASE_URL = "http://ysweb.yonsei.ac.kr:8888/curri120601/curri_pop2.jsp?"
HEADERS = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])


# search_code 불러오기
f =  open("./source/search_code.json", 'r', encoding='utf8')
search_code = json.loads(f.read())
f.close()


# finished_obj 불러오기
# 시간이 꽤 많이 소요되므로 개선이 필요하다.
finished_filename = TARGET_SEMESTER + "-FINISHED_SYLLABUS_OBJS"
LOG.info("작업완료된 강의 객체 목록 다운로드 시작")
if not os.path.isfile(f'./source/{finished_filename}.txt'):
    f = open(f'./source/{finished_filename}.txt', 'w', encoding='utf8')
    f.close()
    FINISHED_SYLLABUS_OBJS = refresh_finished_syllabus(TARGET_SEMESTER)
else:
    # refresh 하기
    FINISHED_SYLLABUS_OBJS = refresh_finished_syllabus(TARGET_SEMESTER)
    f =  open(f'./source/{finished_filename}.txt', 'w', encoding="utf8")
    for obj_codename in FINISHED_SYLLABUS_OBJS:
        f.write(obj_codename)
        f.write("\n")
    f.close()
LOG.info("작업완료된 강의 객체 목록 다운로드 완료")


def recordError(func):
    def wrapper(*args):
        try:
            func(*args)
        except:
            LOG.info(traceback.format_exc())
    return wrapper


def random_sleep():
    time.sleep(random.random() * 2 + 1)

def create_syllabus_data(soup):
    txtbook_key = "landisplay(_texts)"
    lectname_key = "landisplay(_kna)"
    lectname = None
    jsonData = None

    table = soup.findAll("form", { "name" : "myForm" })[0].findAll("table")[1]
    tr_lst = table.findAll("tr")
    for tr in tr_lst:
        td_lst = tr.findAll("td")
        script = td_lst[0].find("script")
        if lectname_key in str(script):
            lectname = td_lst[1].text.strip()
        elif txtbook_key in str(script):
            raw_data = td_lst[1].find("pre").text.split('\n')
            data = [line.replace('\t', '') for line in raw_data if line != '\t']
        else:
            pass

    if lectname and data:
        jsonData = {"교재 및 참고문헌": data}
        return lectname, jsonData
    else:
        return None, None


# last page 여부와 해당 페이지의 강의 수를
# tuple로 반환
def check_page_info(driver, selector):
    page_raw = driver.find_element_by_css_selector(selector['page_info']).text
    reg = r'\d+-\d+\sof\s\d+'
    validated = re.match(reg, page_raw)
    if validated:
        page_info = validated.group()

        if page_info == "1-15 of 0":
            return False, 'invalid'

        page_start  = re.match(r'\d+-\d+\b', page_info).group().split('-')[0]
        page_now    = re.match(r'\d+-\d+\b', page_info).group().split('-')[-1]
        page_end    = re.search(r' of [\d]+', page_info).group().split(' ')[-1]

        try:
            rows_in_page = int(page_now) - int(page_start) + 1
            LOG.info(f'{rows_in_page} rows in {page_info}')
        except:
            raise Exception("Wrong Text type")        


        if int(page_now) == int(page_end):
            return (True, rows_in_page)
        else:
            return (False, rows_in_page)
    else:
        raise Exception("Wrong Page Text")


def push_data_to_file(lect_name, jsonData, path_ohakkwa, obj_code ):

    if not lect_name or not jsonData:
        return f'{obj_code} has invalid name or data. 수집 중단'

    fpath = path_ohakkwa + "/" + obj_code + ".json"
    # fpath = 'result.json'
    # 기존에 파일이 있는지 확인
    if os.path.isfile(fpath):
        f = open(fpath, 'r', encoding='utf8')
        old_data = json.load(f)
        f.close()
        if TARGET_SEMESTER in old_data:
            old_lect_name = old_data[TARGET_SEMESTER]['LECT_DATA']['과목명']
            old_obj_code = old_data[TARGET_SEMESTER]['LECT_DATA']['학정번호-분반-실습']

            if old_lect_name == lect_name:
                if old_obj_code == obj_code:
                    if 'SYLLABUS_DATA' in old_data[TARGET_SEMESTER]:
                        pass
                    else:
                        old_data[TARGET_SEMESTER].update({"SYLLABUS_DATA":jsonData})
                else:
                    return f'{obj_code} != {old_obj_code}. data not safe. 수집 중단'
            else:
                return f'{lect_name} != {old_lect_name}. data not safe. 수집 중단'
        else:
            old_data.update({TARGET_SEMESTER: {"LECT_DATA":{"학정번호" : obj_code,"과목명" : lect_name}, "SYLLABUS_DATA":jsonData}})
        
        # 업데이트 한 data를 파일에 push
        jsonBuffer = json.dumps(old_data, ensure_ascii=False, indent=2)
        f = open(fpath, 'w', encoding="utf8")
        f.write(jsonBuffer)
        f.close()

    else:
        targetData = {TARGET_SEMESTER: {
            "LECT_DATA":{
                "학정번호-분반-실습" : obj_code,
                "과목명" : lect_name
                }, 
                "SYLLABUS_DATA":jsonData
                }}
        jsonBuffer = json.dumps(targetData, ensure_ascii=False, indent=2)
        f = open(fpath, 'w', encoding='utf8')
        f.write(jsonBuffer)
        f.close()

    
    return f'{obj_code} 수집 완료'
    

input_category = ''


@recordError
def CRAWLER(driver):
    while True:
        global input_category
        input_category = input("[MAJORS/MEDICALS/SPECIALS/ELECTIVES/SEARCH] : ")
        if input_category in CATEGOIRES:
            break
        else:
            print("잘못된 카테고리 입력입니다.")

    LOG.info(f'{TARGET_SEMESTER}-{input_category} 수집 시작')
    
    # 단과대/대분류 루프
    for input_ocode1 in globals()[input_category]:
        arg_ocode1      = f'#OCODE1 > option[value="{search_code[input_ocode1]["OCODE1"]}"]'
        path_ocode1     = f'./data/{input_ocode1}'
        if not os.path.isdir(path_ocode1):
            os.mkdir(path_ocode1)
        
        # 단과대 search_code key를 제외한 나머지
        # 학과/소분류만 루프 돌릴 대상임.
        arr_ohakkwa = [key for key in search_code[input_ocode1] if key != 'OCODE1']


        # 학과/소분류 루프
        for input_ohakkwa in arr_ohakkwa:
            LOG.info(f'{TARGET_SEMESTER}-{input_ocode1}-{input_ohakkwa} 수집 시작')

            arg_ohakkwa     = f'#S2 > option[value="{search_code[input_ocode1][input_ohakkwa]}"]'
            path_ohakkwa    = f'./data/{input_ocode1}/{input_ohakkwa}'

            if not os.path.isdir(path_ohakkwa):
                os.mkdir(path_ohakkwa)
            
            # 해당 학과/소분류 최초 페이지 도착
            driver.find_element_by_css_selector(f'{selector["HY"]} > option[value="{TARGET_YEAR}"]').click()
            driver.find_element_by_css_selector(f'{selector["HG"]} > option[value="{TARGET_HG}"]').click()
            driver.find_element_by_css_selector(arg_ocode1).click()
            driver.find_element_by_css_selector(arg_ohakkwa).click()
            driver.find_element_by_css_selector(selector['search_btn']).click()
            driver.implicitly_wait(10)

            while True:
                # 페이지 체크
                # 네트워크 지연 문제로
                # 정확한 page 데이터를 받을 때까지 loop
                while True:
                    time.sleep(0.5)
                    isLastPage, rows_in_page = check_page_info(driver, selector)
                    # 만약 '1-15 of 0'이 나오면 rows_in_page를
                    # invalid로 반환.
                    if rows_in_page=='invalid':
                        time.sleep(0.1)
                    else:
                        break


                # 최초 학과 페이지에 아무 강좌도 없다면 바로 다음 학과/소분류로 이동
                if isLastPage and rows_in_page == 0:
                    LOG.info(f'{input_ohakkwa} has no lectures.')

                    # 다음 학과/소분류로 넘어가기 전 db 부하를 줄이기 위해 1초 이상 랜덤 휴식
                    random_sleep()
                    break

                # 해당 페이지의 lect object 목록 추출
                lects = driver.find_elements_by_css_selector(selector['lect_list'])

                # 페이지 내의 각 강의 lect_obj의 syllabus 수집 시작
                for idx, lect in enumerate(lects):
                    if idx > (rows_in_page - 1):
                        # 수강편람 사이트는 강의가 있으나 없으나 row를 무조건 15개를 고정적으로 
                        # 생성하므로 강의 수를 초과하면 루프를 중단해야 한다.
                        # 강의 수가 0개인 경우에는 위에서 분기 처리를 함.
                        break

                    obj_code = lect.find_element_by_css_selector('div:nth-child(7) > span').text.strip()

                    # 이미 해당 과목에 대한 데이터를 수집한 경우, 중복 방지
                    if obj_code in FINISHED_SYLLABUS_OBJS:
                        already_crwaled = True
                    else:
                        already_crwaled = False

                    if already_crwaled:
                        LOG.info(f"{obj_code}: 중복된 강의 객체. ")

                        # 해당 강의 객체에 대한 수집을 끝내므로 db 부하를 줄이기 위해 1초 이상 랜덤 휴식
                        # 너무 느려서 0.1초 휴식으로 바꿈.
                        # 어차피 넘어가면서 요청 전송은 안 하니까.
                        time.sleep(0.1)
                        pass

                    # 중복이 아닌 경우 해당 강의 object의 수업계획서 수집 시작
                    else:
                        # 수업계획서 링크 parsing 및 validating
                        raw_args = lect.find_element_by_css_selector('div:nth-child(7) > span > a:nth-child(3)').get_attribute('href')

                        # args는 아래와 같은 형식으로 나와야 한다.
                        # ['"H1"', '"CSI2102"', '"01"', '"00"', '"04204"', '"2020"', '"2"', '"0"']
                        # 마지막 인수가 무엇을 의미하는지는 잘 모르겠다.
                        args = [arg.replace('\"', '') for arg in re.findall(r'\"[\w]+\"', raw_args) if ',' not in arg]
                        if len(args) != 8:
                            LOG.info(f'{obj_code} has wrong args.')
                            LOG.info(f'{obj_code} has', args)
                            has_error = True
                        else:
                            targetURL = []
                            targetURL.append(BASE_URL)
                            targetURL.append('&hakno=' + args[1])
                            targetURL.append('&bb=' + args[2])
                            targetURL.append('&sbb=' + args[3])
                            targetURL.append('&domain=' + args[0])
                            targetURL.append('&startyy='+ args[5])
                            targetURL.append('&hakgi=' + args[6])
                            targetURL.append('&ohak=' + args[4])
                            targetURL = ''.join(targetURL)
                            has_error = False

                        if has_error:
                            # 다음 강의로 넘어가므로 db 부하를 줄이기 위해 1초 이상 랜덤 휴식
                            random_sleep()
                            pass
                        else:
                            req = requests.get(targetURL, headers=HEADERS)
                            
                            # 해당 강의 object의 수업계획서 수집 완료 전
                            # 미리 db 부하를 줄이기 위해 1초 이상 랜덤 휴식
                            random_sleep()

                            soup = BeautifulSoup(req.text, 'html.parser')
                            lectname, jsonData = create_syllabus_data(soup)

                            message = push_data_to_file(lectname, jsonData, path_ohakkwa, obj_code )
                            if message:
                                LOG.info(message)
                            else:
                                LOG.info(f"{obj_code} has some problem in pushing data to file")
                                

                            # 끝나면 FINISHED_SYLLABUS_OBJS에 등록
                            FINISHED_SYLLABUS_OBJS.append(obj_code)


                # 현재 페이지에 강의는 있었지만 현재 페이지가 학과/소분류의 마지막 페이지인 경우
                if isLastPage:
                    LOG.info(f'{input_ohakkwa} 수업계획서 수집 완료')

                    # 다음 학과/소분류로 넘어가기 전 db 부하를 줄이기 위해 1초 이상 랜덤 휴식
                    random_sleep()
                    break

                # 해당 페이지의 모든 강의 obj들을 수집했으면 페이지 넘기기
                # 페이지 내 마지막 강의 객체에서 휴식했으므로 별도의 휴식은 없음.
                driver.find_element_by_css_selector(selector['next_page_btn']).click()
                driver.implicitly_wait(10)

        # 단과대/대분류 수업계획서 수집 종료
        LOG.info(f'{input_ocode1} 수집 완료')
        
        # 단과대/대분류 단위에서는 무조건 휴식
        random_sleep()


if __name__ == "__main__":
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.minimize_window()
    driver.get('http://ysweb.yonsei.ac.kr:8888/curri120601/curri_new.jsp#top')
    driver.implicitly_wait(10)
    CRAWLER(driver)

    with open(f'./source/{finished_filename}.txt', 'w', encoding="utf8") as f:
        for obj_codename in FINISHED_SYLLABUS_OBJS:
            f.write(obj_codename)
            f.write("\n")
        f.close()

    LOG.info(f'FINISHED_SYLLABUS_OBJS에 {TARGET_SEMESTER}-{input_category} 전부 등록 완료')