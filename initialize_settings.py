from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import json, time

## 전역 변수
TARGET_YEAR     = '2020'
TARGET_HG       = '2'           # 정수
TARGET_SEMESTER = TARGET_YEAR + TARGET_HG

RESULT_URL = "http://ysweb.yonsei.ac.kr:8888/curri120601/curri_pop_mileage_result01.jsp"
HEADERS = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
driver.get('http://ysweb.yonsei.ac.kr:8888/curri120601/curri_new.jsp#top')

# 각 element들의 selector 목록
selector = {
    "HY"    :"#HY",             # 연도
    "HG"    :"#HG",             # 학기
    "OCODE0":"#OCODE0",         # 학부
    "OCODE1":"#OCODE1",         # 단과대학 및 교양 대분류
    "S2"    :"#S2",             # 학과 및 교양 소분류
    "search_btn"    :'a[href="javascript:searchGb(\'search\',1);"]',
    "next_page_btn" :"#jqxWidget312897233db2 > div",
    "page_info"     :"#pager > div > div > div:nth-child(3)"
}

# 1. 검색 코드 데이터 초기화
def initialize_search_code(driver):
    '''
    연세포탈서비스 > 학부/대학원 수강편람조회 > http://ysweb.yonsei.ac.kr:8888/curri120601/curri_new.jsp#top에서
    각 select > option 태그들을 일일히 선택해가며
    검색 (분류) 코드들을 정리하는 함수이다.

    굳이 넣어봐야 데이터가 없거나 다른 종별과 완벽하게 겹쳐서
    리소스만 잡아먹는다고 판단한 코드들은 json 파일에서 직접 제거하였다.
    
    2020-11-10 search_code.json에서 학부, (~2007)국제교육부, 계절학기 삭제
    2020-11-09 디렉토리를 만드는 과정에서 '/'가 들어간 string이 있었는데
               2010년 이전 항목이어서 그냥 모두 삭제함.
    2020-11-12 법학대학은 2017년 이후 개설과목이 없어서 모두 삭제

               스포츠레저학전공은 전공명이 스포츠응용산업전공으로 변경됨.
               학정번호가 같기 때문에 2016년까지만 수집 후
               삭제하는 것이 바람직하다.

               간호대학 > 계절학기(간호대학) 삭제
               간호대학은 전공자 대상 수업임에도 마일리지 결과에 전공자/복수전공자가
               모두 N (N)으로 나와서 전공자/비전공자를 가르기가 매우 힘들다.

               2009년학번 이전의 분류에 대해서는 모두 삭제

               이과대학 > 의예과(~2011)
               이과대학 > 치의예과(~2011)
               이과대학 > 자연과학부
               공과대학 > (~2008)금속시스템공학전공
               공과대학 > (~2008)세라믹공학전공
               공과대학 > (~2016)정보산업공학전공
               사회과학대학 > (~2010)신문방송학전공
               음악대학 > 음악대학(~2015)
               언더우드국제대학 > (~2010)국제교육부-국제교육부
               언더우드국제대학 > (~2010)국제교육부-대학원(일반/GSISMBA)
               언더우드국제대학 > (~2010)국제교육부-한국어학당
               학부기초(~2009학번)
               학부필수(~2009학번)
               계열기초(~2009학번)
               학부선택(~2009학번)
               국제캠퍼스(2019학번~) > 기초교육-YONSEI RC 101
               국제캠퍼스(2019학번~) > 기초교육-RC운영교과
               국제캠퍼스(2019학번~) > 전공
               (~2018학번)국제캠퍼스 > 선택교양-YONSEI RC 101
               (~2018학번)국제캠퍼스 > 선택교양-RC 기타
               (~2018학번)국제캠퍼스 > 전공
    2020-11-13 각 대분류
               국제캠퍼스(~2018학번) > 전공 : "1870"
               국제캠퍼스(2019학번~) > 전공 : "3140"
               에는 타 전공 분류에 없는 강의 객체들이 포함되어 있어서
               다시 seacrh_code.json에 추가하였다.

               하지만 유의사항이 모두 font 태그로 되어 있어 유의사항 standard 자체를
               CRAWLER가 읽지 못하고 페이지를 통째로 스킵하는 상황이 발생하였다.
               따라서 각 대분류의 '전공'은 우선 search_code.json에서 다시 삭제하고,
               추후 생각을 해봐야할 듯 하다.
    
    2020-11-15 2016년의 강의 객체들을 모두 수집했으므로,
               "(~2016)스포츠레저학전공": "1003"
               는 삭제함.

    2020-11-25 국내교환대학 삭제
               계절학기 삭제

    '''

    # 1-1. OCODE0의 모든 option들을 가져오기
    ocodes_raw = driver.find_elements_by_css_selector('#OCODE1 > option[value]')
    ocodes = [ocode_raw.get_attribute("value") for ocode_raw in ocodes_raw]

    # 1-2. OCODE1의 하위 목록들을 수집
    data = {}
    for ocode in ocodes:
        instance_OCODE1 = driver.find_element_by_css_selector(f'#OCODE1 > option[value="{ocode}"]')
        instance_OCODE1.click()
        time.sleep(2)       # 충분한 대기 시간 설정

        arr = driver.find_elements_by_css_selector(f'#S2 > option[value]')
        obj = {"OCODE1":ocode}
        for option in arr:
            if option.get_attribute("value") == "all":
                pass
            else:
                obj[option.text] = option.get_attribute("value")
        data[instance_OCODE1.text] = obj

    # 1-3. json으로 저장
    with open("./source/search_code.json", 'w', encoding='utf8') as f:
        data = json.dumps(data, ensure_ascii=False)
        f.write(data)
        f.close()

if __name__ == "__main__":
    # test 코드
    initialize_search_code(driver)