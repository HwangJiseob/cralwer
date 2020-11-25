from bs4 import BeautifulSoup
import json, re

__all__ = ['create_lect_data', 'create_lect_result']

def split_majorCap_and_2ndMajor(cell):
    validated = re.match(r"[\d]+\s\([Y|N]\)", cell.text)
    if validated:
        arr = validated.group().split(" ")
        tar = re.findall(r"Y|N", arr[1])
        arr[1] = tar[0]
        return arr
    else:
        majorCap = re.search(r"[\d]+", cell.text)
        secondMaj = re.search(r"\([Y|N]\)", cell.text)
        # 비정상적인 코드이기 때문에 default값을 지정하고
        # reg에 맞는 값이 있으면 입력.
        arr = ["0", "N"]
        if majorCap:
            arr[0] = majorCap.group()
        if secondMaj:
            arr[1] = secondMaj.group()
        return arr

def create_lect_data(soup, reg, cols):
    lect_rows_raw = soup.find_all("table")[1].find_all("tr")[-1].find_all("td")
    # data-safe code
    # index로 특정한 table에 오류가 있을 경우 모든 table을 검색.
    if re.match(reg, lect_rows_raw[0].text)==None:
        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                for td in tr.find_all("td"):
                    if re.match(reg, td.text):
                        lect_rows_raw = tr.find_all("td")
                        # loging 필요
                        break
    idx = 0
    rows = []
    for cell in lect_rows_raw:
        if idx == 8:
            refined = split_majorCap_and_2ndMajor(cell)
            if refined:
                rows.append(refined[0])
                rows.append(refined[1])
            else:
                print("ERROR!!!")
                break
        else:
            rows.append(cell.text)
        idx += 1

    return {col:row for col, row in zip(cols, rows)}

# print(create_lect_data(soup, reg_lect_code, lect_cols))

def split_major_and_bracket(cell):
    validated = re.match(r"[Y|N]\s\([Y|N]\)", cell.text).group()
    if validated:
        arr = validated.split(" ")
        tar = re.findall(r"Y|N", arr[1])
        arr[1] = tar[0]
        return arr
    else:
        return None

def create_lect_result(soup, cols):
    result_rows_raw = soup.find_all("table")[-2].find_all("tr")[1].find_all("tr")

    data = []
    # for cell in result_rows_raw[0].find_all("td"):
    for tr in result_rows_raw:
        idx = 0
        record = []
        for cell in tr.find_all("td"):
            if idx == 2:
                # print(cell)
                refined = split_major_and_bracket(cell)
                if refined:
                    record.append(refined[0])
                    record.append(refined[1])
                else:
                    print("ERROR!!!")   # logging 필요
                    break
            else:
                if cell.text == "\xa0" or "*\xa0" :
                    # 대부분의 경우 기타에 \xa0 값이 들어간다.
                    # Null, None 대신 그냥 "" 넣어준다.
                    record.append(cell.text.replace("\xa0", ""))
                else:
                    # 학교 정책 배려자의 경우, 기타에 \xa0 값이 들어가므로
                    # 이를 뺀 값을 넣어준다.
                    record.append(cell.text)
            idx += 1
        row = {col:cell for col, cell in zip(cols, record)}
        data.append(row)
    return data

# d = create_lect_result(soup, result_cols)
# with open("pub1101.json", 'w', encoding='utf8') as f:
#     f.write(str(d).replace("\'", "\""))
#     f.close()

# sss = pd.read_json('pub1101.json')
# print(sss)




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
            lectname = td_lst[1].text
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