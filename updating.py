import traceback, time, sys, json

MAJORS = ["문과대학", "상경대학", "경영대학", "이과대학", "공과대학", "생명시스템대학",
          "신과대학", "사회과학대학", "음악대학", "생활과학대학", "교육과학대학",
          "언더우드국제대학", "글로벌인재대학"]
MEDICALS = ["약학대학", "의과대학", "치과대학", "간호대학"]
SPECIALS = ["연계전공", "ROTC", "Study Abroad Course", "교직과정", "국내교환대학", 
            "공통"]
ELECTIVES = ["교양기초(2019학번~)", "대학교양(2019학번~)", "기초교육(2019학번~)", "국제캠퍼스(2019학번~)",
             "공통기초(10~18학번)", "필수교양(10~18학번)", "선택교양(10~18학번)", "(~2018학번)국제캠퍼스"]

ALL = MAJORS + MEDICALS + SPECIALS + ELECTIVES

def recordError(func):
    def wrapper():
        try:
            func()
        except:
            print(traceback.format_exc())
    return wrapper

@recordError
def loop_categories():
    return 1/0



# search_code 호출
with open("./source/search_code.json", 'r', encoding='utf8') as f:
  SEARCH_CODE = json.loads(f.read())
  f.close()




INPUT_OPTIONS = ['ALL', 'MAJORS', 'MEDICALS', 'SPECIALS', 'ELECTIVES', 'CUSTOM']

STRING_get_target_semester = """
[TARGET SEMESTER]
크롤링할 학기 입력
(계절학기는 선착순 방식이므로 3, 4는 인수로 받지 않으며
2016년 이전은 검색할 수 없다.)
(예: 20202)
TARGET SEMESTER : """
STRING_get_option= """
[CRAWL OPTION]
ALL       : search_code.json에 있는 모든 ocode1의 모든 학과를 검색
MAJORS    : 문과대학, 상경대학 등
MEDICALS  : 약학대학, 의과대학 등
SPECIALS  : 연계전공, ROTC 등
ELECTIVES : 교양기초 등

CUSTOM    : 특정 ocode1이나 특정 ohakkwa를 크롤링해야 하는 경우
Enter OPTION  : """
STRING_get_custom_options_1_of_2 = """
CUSTOM OPTION(1/2)
Y : 특정 단과대/대분류 선택 (복수 선택 가능)
N : 특정 대분류-소분류에서부터 시작.
CUSTOM OPTION : """
STRING_get_custom_options_2_of_2_v1 = """
CUSTOM OPTION (2/2)
단과대/대분류 세부 선택
복수 선택 시 ","로 구분   (예: 문과대학,상경대학,경영대학)
단과대/대분류 선택: """
STRING_get_custom_options_2_of_2_v2 = """
CUSTOM OPTION (2/2)
시작 단과대/대분류 및 학과/소분류 선택
학과/소분류 선택 안 할 시에는 단과대/대분류만 기재
(예1 : 문과대학)
(예2 : 이과대학-수학전공)
CUSTOM OPTION : """
STRING_get_user_confirmation = """
[USER CONFIRMATION]
TARGET_SEMESTER : {0}
{1}

Confirm   : Y or Enter
Quit      : Q
Press     : """


def get_target_semester():
  input_target_semester = input(STRING_get_target_semester)
  if (len(input_target_semester) == 5 and input_target_semester.isdecimal()
    and input_target_semester[-1] in ['1', '2']
    and int(input_target_semester[:4]) > 2015):
    return input_target_semester
  else:
    print("\nWrong Input")
    return get_target_semester()

def get_option():
  input_option  = input(STRING_get_option)

  if input_option not in INPUT_OPTIONS:
    print("\nWrong input")
    return get_option()

  return ("D", input_option)

def get_custom_options():
  def input_1_of_2():
    custom_options = input(STRING_get_custom_options_1_of_2)
    if custom_options in ["Y", "N"]:
      return custom_options
    else:
      print("\nWrong Input")
      return input_1_of_2()

  def input_2_of_2(option_1_of_2):
    
    if option_1_of_2 == "Y":
      custom_options = input(STRING_get_custom_options_2_of_2_v1)
      selected_ocode1s = custom_options.split(',')
      validated = [o.strip() for o in selected_ocode1s if o in ALL]

      if len(validated) < 1:
        print("\nWrong Input")
        return (option_1_of_2, input_2_of_2(option_1_of_2))
      else:
        print("수집 항목: ", validated)
        return (option_1_of_2, validated)

    if option_1_of_2 == "N":
      custom_options = input(STRING_get_custom_options_2_of_2_v2)
      selected_option = custom_options.split('-')
      selected_option = [x.strip() for x in selected_option]

      if selected_option[0] in ALL:
        if len(selected_option) == 1:
          return (option_1_of_2, selected_option)
        elif len(selected_option) == 2:
          if selected_option[1] in SEARCH_CODE[selected_option[0]]:
            return (option_1_of_2, selected_option)
          else:
            print("\n잘못된 학과/소분류 입력")
            return (option_1_of_2, input_2_of_2(option_1_of_2))
        else:
          print("\nWrong Input")
          return (option_1_of_2, input_2_of_2(option_1_of_2))
      else:
        print("\n잘못된 단과대/대분류 입력")
        return (option_1_of_2, input_2_of_2(option_1_of_2))

  option_1_of_2 = input_1_of_2()
  option_2_of_2 = input_2_of_2(option_1_of_2)

  return option_2_of_2

def get_user_confirmation(input_target_semester, input_option):
    scenario_key, scenario_target = input_option
    if scenario_key == "D":
      second_string = f"TARGET_CATEGORY : {scenario_target}"
    elif scenario_key == "Y":
      second_string = f"TARGET_OCODE1   : {', '.join(scenario_target)}"
    elif scenario_key == "N":
      second_string = f"START_FROM      : {'-'.join(scenario_target)}"
    input_string = STRING_get_user_confirmation.format(input_target_semester, second_string)

    user_confirmation = input(input_string)

    if user_confirmation == "Y" or len(user_confirmation) == 0:
      return "Y"
    elif user_confirmation == "Q":
      print("CRWALER 종료")
      sys.exit()
    else:
      return get_user_confirmation(input_target_semester, input_option)



def get_finished_object_list():
  finished_filename = TARGET_SEMESTER + "-FINISHED_LECT_OBJs"


def open_ysweb_browser():
  pass


# CRAWLER는 generator 함수이다.
def CRAWLER():
  # 1.1 크롤링할 대상 학기 선택
  input_target_semester = get_target_semester()

  # 1.2 크롤링 옵션 선택
  input_option = get_option()

  # 1.3 CUSTOM OPTION일 경우 input_option 수정
  if input_option == ("D", "CUSTOM"):
    input_option = get_custom_options()

  # 1.4 최종 CONFIRM 승인
  if get_user_confirmation(input_target_semester, input_option) == "Y":
    TARGET_SEMESTER = input_target_semester
    TARGET_YEAR     = TARGET_SEMESTER[:4]
    TARGET_HG       = TARGET_SEMESTER[-1]
    SCENARIO_KEY, SCENARIO_TARGET = input_option

  yield None
  
  # for i in range(1, 100):
  #   time.sleep(1)
  #   yield None
  #   print(i)
    

  yield None
  
  # 2. FINISHED OBJECTS 동기화
  

  # 3. selenium으로 포탈에 접속

  # 4. OPTION loop
  if SCENARIO_KEY == "D":
    for input_ocode1 in globals()[SCENARIO_TARGET]:
      # 채워넣어야 함.
      pass
  elif SCENARIO_KEY == "Y":
    for input_ocode1 in SCENARIO_TARGET:
      # 채워넣어야 함.
      pass

  elif SCENARIO_KEY == "N":
    if SCENARIO_TARGET[0] in SEARCH_CODE and len(SCENARIO_TARGET) == 1:
      for idx, input_ocode1 in enumerate(ALL):
        if idx < ALL.index(SCENARIO_TARGET[0]):
          pass
        else:
          # 채워넣어야 함.
          pass
    elif (SCENARIO_TARGET[0] in SEARCH_CODE and len(SCENARIO_TARGET) == 2
      and SCENARIO_TARGET[1] in SEARCH_CODE[SCENARIO_TARGET[0]]):
      for idx, input_ocode1 in enumerate(ALL):
        if idx < ALL.index(SCENARIO_TARGET[0]):
          pass
        elif idx == ALL.index(SCENARIO_TARGET[0]):
          arr = [x for x in SEARCH_CODE[SCENARIO_TARGET[0]] if x != "OCODE1"]
          for jdx, input_ohakkwa in enumerate(arr):
            if jdx < arr.index(SCENARIO_TARGET[1]):
              pass
            else:
              # 채워넣어야 함.
        else:
          # 채워넣어야 함.
      # 구현하기 빡세네
    else:
      print("에러 발생 ")
  # 5. ocode1 loop
  # 6. ohakkwa loop
  # 7. page loop
  # 7.1   page의 유의사항 찾기
  # 7.2   page의 강의 수 찾기
  # 7.3   page 
  # 8. 강의 object loop
  # 8.1   중복 강의 확인
  # 8.2   중복 강의가 아니면 유의사항과 mileage 결과 넣기
  # 9. FINISHED OBJECTS에 삽입.



if __name__ == "__main__":
    steps = CRAWLER()
    for i in steps:
      i