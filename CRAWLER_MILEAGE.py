from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


from bs4 import BeautifulSoup
import json, time, requests, re, os, csv, signal

from modules.dataIterator import *
from modules.resultParser import *
from modules.logger import *
from modules.cautionParser import *

LOG = StandardLogger().get_logger()

## 전역 변수
TARGET_YEAR     = '2020'
TARGET_HG       = '2'           # 정수

## 만약 TARGET_SEMESTER도 입력할 경우
TARGET_YEAR     = input("TARGET_YEAR(ex: 2020)  : ")
TARGET_HG       = input("TARGET_HG(1 or 2)      : ")

TARGET_SEMESTER = TARGET_YEAR + TARGET_HG



RESULT_URL = "http://ysweb.yonsei.ac.kr:8888/curri120601/curri_pop_mileage_result01.jsp"
CAUTION_BASE_URL = "http://ysweb.yonsei.ac.kr:8888/curri120601/curri_pop5.jsp"
HEADERS = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
# driver = webdriver.Chrome('./source/chromedriver.exe', options=options)
driver.get('http://ysweb.yonsei.ac.kr:8888/curri120601/curri_new.jsp#top')



MAJORS = ["문과대학", "상경대학", "경영대학", "이과대학", "공과대학", "생명시스템대학",
          "신과대학", "사회과학대학", "음악대학", "생활과학대학", "교육과학대학",
          "언더우드국제대학", "글로벌인재대학"]
MEDICALS = ["약학대학", "의과대학", "치과대학", "간호대학"]
SPECIALS = ["연계전공", "ROTC", "Study Abroad Course", "교직과정", "국내교환대학", 
            "공통"]


# 2018년까지만 빼놓고 2019부터는 추가
# "교양기초(2019학번~)", "대학교양(2019학번~)", "기초교육(2019학번~)", "국제캠퍼스(2019학번~)",
ELECTIVES = ["공통기초(10~18학번)", "필수교양(10~18학번)", "선택교양(10~18학번)", "(~2018학번)국제캠퍼스",
             "교양기초(2019학번~)", "대학교양(2019학번~)", "기초교육(2019학번~)", "국제캠퍼스(2019학번~)"]


# 내가 따로 찾아야겠다 싶으면 SEARCH에 ocode1 넣고 cmd에 SEARCH를 입력하면 된다.
SEARCH = []





CATEGORY = {"MAJORS": MAJORS,
            "MEDICALS":MEDICALS,
            "SPECIALS":SPECIALS, 
            # 밑의 코드에서 ALL을 추가함.
            "ELECTIVES":ELECTIVES,
            "SEARCH":SEARCH}

# SEARCH 제외 모든 분류를 ALL 포함
ALL = []
for arr in CATEGORY:
    if arr != "SEARCH":
        for ocode1 in CATEGORY[arr]:
            ALL.append(ocode1)
CATEGORY['ALL'] = ALL




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

# column명 목록
lect_cols = [
    "학정번호-분반-실습",
    "과목명",
    "학점",
    "담당교수",
    "강의시간",
    "강의실",
    "정원",
    "참여인원",
    "전공자정원",
    "2전공포함", # 분리
    "1학년정원",
    "2학년정원",
    "3학년정원",
    "4학년정원",
    "교환학생 가능여부",
    "Max Mileage(limit)",
    "Mileage_minimum",
    "Mileage_maximum",
    "Mileage_average"
]

result_cols = [
    "순위",
    "마일리지",
    "전공자/복수전공자",
    "전공자정원포함여부",   # 분리
    "신청과목수",
    "졸업신청",
    "초수강여부",
    "총이수학점/졸업이수학점",
    "직전학기이수학점/학기당수강학점",
    "학년",
    "수강여부",
    "비고"
]




# 페이지 체크
def page_check(driver, selector):
    page_raw = driver.find_element_by_css_selector(selector['page_info']).text
    reg = r'\d+-\d+\sof\s\d+'
    validated = re.match(reg, page_raw)
    if validated:
        page_info = validated.group()

        page_end = re.search(r' of [\d]+', page_info).group().split(' ')[-1]
        page_now = re.match(r'\d+-\d+\b', page_info).group().split('-')[-1]
        if int(page_now) == int(page_end):
            return False
        else:
            return True
    else:
        raise Exception("Wrong Page Text")

def row_check(driver, selector):
    time.sleep(0.5)
    page_raw = driver.find_element_by_css_selector(selector['page_info']).text
    reg = r'\d+-\d+\sof\s\d+'
    validated = re.match(reg, page_raw)
    if validated:
        page_info = validated.group()

        page_end    = re.search(r' of [\d]+', page_info).group().split(' ')[-1]
        page_now    = re.match(r'\d+-\d+\b', page_info).group().split('-')[-1]
        page_start  = re.match(r'\d+-\d+\b', page_info).group().split('-')[0]

        try:
            rows_in_page = int(page_now) - int(page_start) + 1
            LOG.info(f'{rows_in_page} rows in {page_info}')
            return rows_in_page
        except:
            raise Exception("Wrong Text type")

    else:
        raise Exception("Wrong Page Text")

def search_caution_standard(driver, selector):
    # 검색 테이블 최상단의 유의사항을 통해 수집.
    
    scaution_idx = 0
    while scaution_idx <= row_check(driver, selector):
        caution_sel = "#row"+ str(scaution_idx) +"jqxgrid > " + selector['caution_path']
        try:
            element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, caution_sel)))
            caution_link = driver.find_element_by_css_selector(caution_sel).get_attribute('href')
        except:
            LOG.info(f'No caution link in {scaution_idx}th row')
            caution_link = None
        
        if caution_link:
            reg = r'"\w+"'
            caution_par = re.findall(reg, caution_link)
            caution_par1 = caution_par[0].replace('\"', '')
            caution_par2 = caution_par[1].replace('\"', '')
            caution_par3 = caution_par[2].replace('\"', '')

            CAUTION_URL = CAUTION_BASE_URL + f'?domain={caution_par1}&hyhg={caution_par2}&ohakkwa={caution_par3}'

            req = requests.get(CAUTION_URL, headers=HEADERS)

            soup = BeautifulSoup(req.text, 'html.parser')
            standard = create_caution_standard(soup)

            LOG.info(f'유의사항 기준 탐색 완료')
            return standard
            break
        else:
            pass
        scaution_idx += 1

    LOG.info('No caution in pages')
    return None



# 2. 새학기 lect_object 목록 초기화와 동시에
# 마일리지 결과 데이터 크롤링하기. 

# LOG.info("test Started")


f =  open("./source/search_code.json", 'r', encoding='utf8')
scode = json.loads(f.read())
f.close()


# 이전에 완료한 OBJ들 목록 불러오기
# 수집 끝난 강의 객체들의 목록
finished_filename = TARGET_SEMESTER + "-FINISHED_LECT_OBJs"
LOG.info("작업완료된 강의 객체 목록 다운로드 시작")
if not os.path.isfile(f'./source/{finished_filename}.txt'):
    f = open(f'./source/{finished_filename}.txt', 'w', encoding='utf8')
    f.close()
    FINISHED_LECT_OBJS = refresh_finished_lects(TARGET_SEMESTER)
else:
    # refresh 하기
    FINISHED_LECT_OBJS = refresh_finished_lects(TARGET_SEMESTER)
    f =  open(f'./source/{finished_filename}.txt', 'w', encoding="utf8")
    for obj_codename in FINISHED_LECT_OBJS:
        f.write(obj_codename)
        f.write("\n")
    f.close()
LOG.info("작업완료된 강의 객체 목록 다운로드 완료")



### 단과대 loop 시작
input_category = input("[MAJORS/MEDICALS/SPECIALS/ELECTIVES/SEARCH] : ")
# 루프 중 서버단이나 코드 오류로 프로그램이 멈출 경우,
# 해당 에러를 기록하기 위해 try 코드를 삽입.
try:
    for input_ocode1 in CATEGORY[input_category]:


        # # 단과대 수기 입력 시 코드
        # input_ocode1    = str(input("단과대 혹은 대분류     : "))
        arg_ocode1      = f'#OCODE1 > option[value="{scode[input_ocode1]["OCODE1"]}"]'
        path_ocode1     = f'./data/{input_ocode1}'
        if not os.path.isdir(path_ocode1):
            os.mkdir(path_ocode1)
        # 학과 수기 입력 시 코드 (단과대를 수기 입력해야 사용 가능)
        # input_ohakkwa   = str(input("학과/전공 혹은 소분류  : "))




        # 학과별/소분류별 탐색 시작
        # 첫 번째 인자에 단과대/대분류 search code가 들어있어서
        # 이걸 제외하고 시작한다.
        # 수기 입력 시에는 arr_ohakkwa와 for문을 지우고 indent를 당기면 된다.
        arr_ohakkwa = [key for key in scode[input_ocode1] if key != 'OCODE1']




        for input_ohakkwa in arr_ohakkwa:
            LOG.info(f'{TARGET_SEMESTER}-{input_ocode1}-{input_ohakkwa} 수집 시작')

            arg_ohakkwa     = f'#S2 > option[value="{scode[input_ocode1][input_ohakkwa]}"]'
            path_ohakkwa    = f'./data/{input_ocode1}/{input_ohakkwa}'

            if not os.path.isdir(path_ohakkwa):
                os.mkdir(path_ohakkwa)

            # 2-1.최초 페이지 도착
            driver.find_element_by_css_selector(f'{selector["HY"]} > option[value="{TARGET_YEAR}"]').click()
            driver.find_element_by_css_selector(f'{selector["HG"]} > option[value="{TARGET_HG}"]').click()
            driver.find_element_by_css_selector(arg_ocode1).click()
            driver.find_element_by_css_selector(arg_ohakkwa).click()
            driver.find_element_by_css_selector(selector['search_btn']).click()
            driver.implicitly_wait(10)



            # 2-2. 학과별/소분류별 유의사항 기준 수집
            standard = search_caution_standard(driver, selector)


            # 2-3. 최초 페이지 체크
            looping_pages = page_check(driver, selector)

            # 마지막 페이지가 아니면 페이지 내의 강의 obj 수집 시작
            while True:

                # 2-4. 해당 페이지의 lect object 목록 추출
                lects = driver.find_elements_by_css_selector(selector['lect_list'])

                row_idx = 0
                rows_in_page = row_check(driver, selector)

                # 2-5. 각 강의 obj 수집 시작.
                for lect in lects:
                    row_idx += 1
                        # 수강편람 사이트는 강의가 있으나 없으나 row를 무조건 15개를 생성하므로
                        # 강의 수를 초과하면 루프를 중단해야 한다.
                    if row_idx > rows_in_page:
                        break

                    obj_code = lect.find_element_by_css_selector('div:nth-child(7) > span').text.strip()

                    # 2-5-1. 이미 해당 과목에 대한 데이터를 수집한 경우, 중복 방지
                    if obj_code in FINISHED_LECT_OBJS:
                        already_crwaled = True

                        # 유의사항 수집
                        try:
                            cautionBuffer = parse_cautions(driver, lect, selector['caution_path'], input_ocode1, input_ohakkwa, standard, row_idx)

                            # 기존 데이터 파일에 덮어쓰기
                            fpath = find_lect_in_data_dir(obj_code, TARGET_SEMESTER)
                            with open(fpath, 'r', encoding="utf8") as f:
                                data = json.load(f)

                            '''
                            2020-11-13
                            20171-MAJORS.log에서 STA1001-17-00에 대하여 아래 코드에서 Key Error가 발생함.
                            확인 결과 이전 학기에는 다른 디렉토리에 강의 객체가 있다가 다음 학기에는 다른 디렉토리에
                            강의 객체가 있어서 ./data 하위에 같은 강의 객체 ID를 가진 JSON 파일이 생성된 경우,
                            프로그램 순서상 먼저 확인한 JSON 파일에 해당 TARGET_SEMESTER가 없어서 Key Error가 발생한다.

                            우선 JSON 파일에 TARGET SEMESTER가 없을 때, TARGET_SEMESTER는 있지만 input_ocode1가 없을 때,
                            그리고 둘 다 없는 상황을 세분화하여 각각 잘 

                            그리고 파일이 2개 이상이더라도 문제가 없도록 dataIterator 모듈의 find_lect_in_data_dir 함수에서
                            파일명과 현재 작업 중인 강의 객체 코드명이 같더라도 작업 중인 TARGET_SEMESTER에 해당하지 않으면
                            넘어가도록 코드를 추가했다.

                            추가로 코드가 너무 땜빵질 되어 있어서 많이 걱정된다.
                            '''
                            

                            if TARGET_SEMESTER in data:
                                if input_ocode1 in data[TARGET_SEMESTER]['CAUTION']:
                                    data[TARGET_SEMESTER]['CAUTION'][input_ocode1].update({input_ohakkwa:cautionBuffer})
                                else:
                                    data[TARGET_SEMESTER]['CAUTION'].update({input_ocode1:{input_ohakkwa:cautionBuffer}})
                            else:
                                data[TARGET_SEMESTER] = {"CAUTION":{input_ocode1:{input_ohakkwa:cautionBuffer}}}

                            dumpBuffer = json.dumps(data, ensure_ascii=False, indent=2)
                            
                            with open(fpath, 'w', encoding="utf8") as f:
                                f.write(dumpBuffer)
                                f.close()
                            LOG.info(f"{obj_code}: 중복된 강의 객체. caution 수집 완료")
                        except:
                            LOG.info({traceback.format_exc()})
                            # LOG.info(f"{obj_code}: {exclog(traceback.format_exc())}")
                    else:
                        already_crwaled = False

                        
                    # 2-5-2. 마일리지 결과가 실재하는지 확인
                    if already_crwaled:
                        pass
                    else:
                        # 백엔드 서버에서 마일리지 결과 페이지를 강제로 새 창에 띄우므로
                        # requests 모듈을 써서 따로 html 결과를 가져옴.

                        splited = obj_code.split("-")
                        if input_ocode1 == "의과대학":
                            yshs_domain = "H7"
                        elif input_ocode1 == "치과과대학":
                            yshs_domain = "H8"
                        elif input_ocode1 == "간호대학":
                            yshs_domain = "H9"
                        else:
                            yshs_domain = "H1"
                        data = {"yshs_domain":yshs_domain, "yshs_hyhg":TARGET_SEMESTER, "yshs_hakno":splited[0], "yshs_bb":splited[1], "yshs_sbb":splited[2]}
                        req = requests.get(RESULT_URL, headers=HEADERS, data=data) # json=data로 할 때는 왜 안 될까.

                        soup = BeautifulSoup(req.text, 'html.parser')
                        center = soup.find('center')

                        # mileage 결과는 center 태그의 존재 유무로 결정
                        # 이런 방식은 틀릴 가능성이 높기 때문에 항상 주의해야 한다.
                        if center != None:
                            mileage_confirmed = False
                            # DB 부하 줄이기
                            time.sleep(0.5)
                        else:
                    # 2-5-3. mileage 결과가 존재하면 parsing해서 json으로 저장
                            targetJson = {}
                            jsonBuffer = {}

                            # 유의사항 수집
                            try:
                                cautionBuffer = parse_cautions(driver, lect, selector['caution_path'], input_ocode1, input_ohakkwa, standard, row_idx)
                            except:
                                cautionBuffer = {}

                            # LECT_DATA와 RESULT_DATA 수집
                            # 뒤에 &nbsp 붙은 학정코드가 존재함.
                            reg_lect_code = r"\b[A-Z]{3}[0-9]{4}\b"
                            lect_data = create_lect_data(soup, reg_lect_code, lect_cols)
                            lect_result = create_lect_result(soup, result_cols)

                            # 하나의 dict로 합치기
                            jsonBuffer = {
                                    "CAUTION":{input_ocode1:{input_ohakkwa: cautionBuffer}},
                                    "LECT_DATA":lect_data,
                                    "RESULT_DATA":lect_result,
                                }

                            # 파일에 저장.
                            fpath = path_ohakkwa + "/" + obj_code + ".json"
                            if os.path.isfile(fpath):
                                # 기존에 파일이 있을 경우, SEMESTSER 객체를 추가하거나
                                # 기존에 같은 SEMESTER 객체가 있으면 덮어쓴다.(json.update 특징)
                                with open(fpath, 'r', encoding='utf8') as f:
                                    old_data = json.load(f)
                                old_data.update({TARGET_SEMESTER:jsonBuffer})
                                dumpBuffer = json.dumps(old_data, ensure_ascii=False, indent=2)
                                with open(fpath, 'w', encoding='utf8') as f:
                                    f.write(dumpBuffer)
                                    f.close()
                            else:
                                newBuffer = {TARGET_SEMESTER:jsonBuffer}
                                dumpBuffer = json.dumps(newBuffer, ensure_ascii=False, indent=2)
                                with open(fpath, 'w', encoding="utf8") as f:
                                    f.write(dumpBuffer)
                                    f.close()

                    # 2-5-4. 강의 obj 수집이 끝나면 FINISHED_LECT_OBJS에 등록
                            FINISHED_LECT_OBJS.append(obj_code)

                    # 2-5-5. DB 부하를 줄이기 위한 강제 휴식 및 최종 종료 로그 선언
                            time.sleep(2)
                            LOG.info(f'{obj_code} cleared')

                # 2-6. 해당 페이지의 모든 강의 obj들을 수집했으면
                # 페이지 넘기기
                time.sleep(2)
                driver.find_element_by_css_selector(selector['next_page_btn']).click()
                driver.implicitly_wait(10)


                if looping_pages == False:
                    LOG.info(f'{input_ohakkwa} 탐색 완료')
                    break

                # 2-7. 페이지 넘긴 후 페이지 체크
                looping_pages = page_check(driver, selector)


                # 2-8. 이전 페이지에서 유의사항 링크가 전혀 없었다면
                # 다음 페이지에서 다시 한 번 체크.
                if not standard:
                    standard = search_caution_standard(driver, selector)

        LOG.info(f'{input_ocode1} 수집 완료')


except:
    ### 모든 루프가 끝난 후 실행해야할 코드
    LOG.info(traceback.format_exc())

with open(f'./source/{finished_filename}.txt', 'w', encoding="utf8") as f:
    for obj_codename in FINISHED_LECT_OBJS:
        f.write(obj_codename)
        f.write("\n")
    f.close()

LOG.info(f'FINISHED_LECT_OBJs에 {TARGET_SEMESTER}-{input_category} 전부 등록 완료')