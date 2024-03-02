'''
@Description:针对动态网页的网络爬虫
@Date       :2022/01/11 14:24:13
@Author     :Anatomical
@version    :1.0
'''
# Chrome版本 97.0.4692.71 (正式版本)
# Chromedriver 文件位置"E:\Miniconda3\Scripts"
import logging
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ChromeOptions

import json
from os import makedirs
from os.path import exists
RESULTS_DIR = 'results'
exists(RESULTS_DIR) or makedirs(RESULTS_DIR)

# 定义日志配置
logging.basicConfig(level=logging.INFO,
                    format='%(actime)s - %(levelname)s - %(message)s')
# 目标网站主页
INDEX_URL = 'https://www.8684.cn/'
# 显式等待时间
TIME_OUT = 10

datadict = {'上海': {'上海': {'py': 'shanghai'}}, '江苏': {'南京': {'py': 'nanjing'}, '苏州': {'py': 'suzhou'}, '常州': {'py': 'changzhou'}, '连云港': {'py': 'lianyungang'}, '南通': {'py': 'nantong'}, '徐州': {'py': 'xuzhou'}, '泰州': {'py': 'taizhou'}, '扬州': {'py': 'yangzhou'}, '无锡': {'py': 'wuxi'}, '镇江': {'py': 'zhenjiang'}, '淮安': {'py': 'huaian'}, '盐城': {'py': 'yancheng'}, '宿迁': {'py': 'suqian'}}, '浙江': {'杭州': {'py': 'hangzhou'}, '嘉兴': {'py': 'jiaxing'}, '宁波': {'py': 'ningbo'}, '湖州': {'py': 'huzhou'}, '绍兴': {'py': 'shaoxing'}, '温州': {'py': 'wenzhou'}, '舟山': {
    'py': 'zhoushan'}, '金华': {'py': 'jinhua'}, '台州': {'py': 'taizhou2'}, '衢州': {'py': 'quzhou'}, '丽水': {'py': 'lishui'}}, '安徽': {'合肥': {'py': 'hefei'}, '马鞍山': {'py': 'maanshan'}, '六安': {'py': 'liuan'}, '安庆': {'py': 'anqing'}, '宣城': {'py': 'xuancheng'}, '宿州': {'py': 'suzhou2'}, '池州': {'py': 'chizhou'}, '淮北': {'py': 'huaibei'}, '淮南': {'py': 'huainan'}, '滁州': {'py': 'chuzhou'}, '芜湖': {'py': 'wuhu'}, '蚌埠': {'py': 'bengbu'}, '铜陵': {'py': 'tongling'}, '阜阳': {'py': 'fuyang'}, '黄山': {'py': 'huangshan'}, '亳州': {'py': 'bozhou'}}}

option = ChromeOptions()
# 控制图片的加载来提速
prefs = {
    'profile.default_content_setting_values': {
        'images': 2
    }
}
option.add_experimental_option('prefs', prefs)
# selenium反屏蔽
option.add_experimental_option('excludeSwitches', ['enable-automation'])
option.add_experimental_option('useAutomationExtension', False)
browser = webdriver.Chrome(options=option)
wait = WebDriverWait(browser, TIME_OUT)
browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
})


def scrape_page(url, condition, locator):
    '''
    @description:
    通用的爬取方法，可以对任意URL进行爬取、状态监听以及异常处理
    如果到规定时间还没有加载出对应的节点，就抛出异常并输出错误日志
    @param:
    url:需要爬取页面的URL,condition:页面加载成功的判断条件,locator:定位器
    @return:
    None
    '''
    logging.info('scraping %s', url)
    try:
        browser.get(url)
        wait.until(condition(locator))
    except TimeoutException:
        logging.error('error occurred while scraping %s', url, exc_info=True)


def scrape_totalpage(url):
    '''
    @description:
    显式等待检索选项框按钮的加载，
    以获取检索项的个数以确定翻页的次数
    @param:
    url:检索项第一项页面的url
    @return:
    None
    '''
    scrape_page(url, condition=EC.element_to_be_clickable,
                locator=(By.XPATH, '//*[@id="view_0"]/div/div[1]/div'))


def parse_totalpage():
    '''
    @description:
    根据检索项获取翻页的次数并返回翻页次数
    @param:
    None
    @return:
    totalpage:翻页次数
    '''
    button = browser.find_element_by_xpath('//*[@id="view_0"]/div/div[1]/div')
    button.click()
    browser.implicitly_wait(5)

    totalpage = len(browser.find_element_by_xpath(
        '//*[@id="ccContentTooltip"]/div/div[2]').find_elements_by_tag_name('a'))
    return totalpage


def scrape_busstopBYpage(url):
    '''
    @description:
    显式等待目标检索项页面的每一个站点的标签加载，
    以按照检项的url获取
    @param:
    url:目标检索项的url
    @return:
    None
    '''
    scrape_page(url, condition=EC.presence_of_all_elements_located,
                locator=(By.TAG_NAME, 'wbfspan'))


def parse_busstopBYpage():
    '''
    @description:
    获取一个检索项下的所有车站名称
    @param:
    None
    @return:
    以字符串列表形式返回
    '''
    busstop_a_tags = browser.find_element_by_xpath(
        '//*[@id="view_0"]/div/div[2]').find_elements_by_tag_name('a')
    return [a_tag.get_attribute('title') for a_tag in busstop_a_tags]


def save2json(data):
    '''
    @description:
    将爬取结果保存为json
    @param:
    data:爬取结果
    @return:
    None
    '''
    name = 'bus_stops'
    data_path = f'{RESULTS_DIR}/{name}.json'
    json.dump(data, open(data_path, 'w', encoding='utf8'),
            ensure_ascii=False, indent=2)


def main():
    try:
        for province, pdicrt in datadict.items():
            for city, cdict in pdicrt.items():
                # 按照规律拼出url
                url = 'https://{}.8684.cn/'.format(cdict['py'])

                # 根据检索项获取翻页次数
                scrape_totalpage(url+'sitemap1')
                totalpage = parse_totalpage()

                # 初始化该城市公交站列表
                busstoplist = []

                # 按照检索项（数字、A、B、C...Y、Z）爬取该市公交站点
                for page in range(1, totalpage+1):
                    page_url = url+'sitemap'+str(page)
                    scrape_busstopBYpage(page_url)
                    page_bussstoplist = parse_busstopBYpage()
                    busstoplist.extend(page_bussstoplist)
                datadict[province][city]['bus_stop'] = busstoplist
                
        save2json(datadict)
    finally:
        browser.close()


if __name__ == '__main__':
    main()
