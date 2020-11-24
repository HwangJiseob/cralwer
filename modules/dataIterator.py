import os, re, time, json


def find_lect_in_data_dir(obj_code, TARGET_SEMESTER):
    filename = obj_code + ".json"
    found = False
    list_ocode1 = os.listdir('./data')
    for dir_ocode1 in list_ocode1:
        list_ohakkwa = os.listdir(f'./data/{dir_ocode1}')
        for dir_ohakkwa in list_ohakkwa:
            list_jsons = os.listdir(f'./data/{dir_ocode1}/{dir_ohakkwa}')
            for lect in list_jsons:
                target = re.search(filename, lect)
                if target:
                    fpath = f'./data/{dir_ocode1}/{dir_ohakkwa}/{target.group()}'
                    f = open(fpath, 'r', encoding='utf8')
                    data = json.load(f)
                    f.close()
                    if TARGET_SEMESTER in data:
                        return fpath


def refresh_finished_lects(TARGET_SEMESTER):
    FINISHED_LECTS = []
    for dir_ocode1 in os.listdir('./data'):
        for dir_ohakkwa in os.listdir(f'./data/{dir_ocode1}'):
            for lect_file in os.listdir(f'./data/{dir_ocode1}/{dir_ohakkwa}'):
                f = open(f'./data/{dir_ocode1}/{dir_ohakkwa}/{lect_file}', encoding="utf8")
                data = json.load(f)
                f.close()
                if TARGET_SEMESTER in data:
                    FINISHED_LECTS.append(lect_file.replace('.json', ''))
                else:
                    pass
    return FINISHED_LECTS



if __name__ == "__main__":
    # test
    refresh_finished_lects()
    # obj_code = "BIZ1101-03-00"
    # fpath = find_lect_in_data_dir(obj_code)
    # print("fpath: ", fpath)