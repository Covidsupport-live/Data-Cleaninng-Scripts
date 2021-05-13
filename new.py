from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.support.ui import WebDriverWait
import os,time,re,math
from selenium.common.exceptions import StaleElementReferenceException


# Pre-processed datas to match with current backend system
using_district_list = {
    "ALIPURDUAR": 719,
    "BANKURA": 720,
    "BIRBHUM": 721,
    "COOCHBEHAR": 722,
    "DAKSHIN 24 PARGANA": 740,
    "DAKSHIN DINAJPUR": 723,
    "DARJEELING": 724,
    "HOOGHLY": 725,
    "HOWRAH": 726,
    "JALPAIGURI": 727,
    "JHARGRAM": 728,
    "KALIMPONG": 729,
    "KOLKATA METROPOLITAN AREA": 730,
    "MALDA": 731,
    "MURSHIDABAD": 732,
    "NADIA": 733,
    "PASCHIM BARDHAMAN": 735,
    "PASCHIM MEDINIPUR": 736,
    "PURBA BARDHHAMAN": 737,
    "PURBA MEDINIPUR": 738,
    "PURULIA": 739,
    "UTTAR 24 PARGANA": 734,
    "UTTAR DINAJPUR": 741
}

using_hospital_type={
    "Government Hospital": {
        "dbkey": "govt",
        "webkey": 1
    },
    "Govt. Requisitioned Pvt. Hospital": {
        "dbkey": "pvtundergovt",
        "webkey": 2
    },
    "Private Hospital": {
        "dbkey": "private",
        "webkey": 3
    }
}

# Config
PATH_TO_DRIVER = r'/usr/bin/chromedriver'
endpoint = 'https://excise.wb.gov.in/CHMS/Public/Page/CHMS_Public_Hospital_Bed_Availability.aspx'


chrome_options = Options()
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--window-size=1920x1080")


#Functions

#Init
def init_scrape(chrome_options,endpoint,PATH_TO_DRIVER=r'/usr/bin/chromedriver'):
    driver = webdriver.Chrome(executable_path = PATH_TO_DRIVER, options=chrome_options)
    driver.get(endpoint)
    wait = WebDriverWait(driver,20)
    wait.until(EC.element_to_be_clickable((By.ID,"ctl00_ContentPlaceHolder1_ddl_District")))
    return driver,wait

# Track the loading spinner
def still_loading(driver,wait):
    try:
        return driver.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_upPgo"]').value_of_css_property("display")
    except:
        return "done"
    
    
# Select Radio Buttons
def select_hospital_type(driver,label):
    try:
        radio = driver.find_element_by_xpath("//*[@id='ctl00_ContentPlaceHolder1_rdo_Govt_Flag']/label[{}]".format(str(label)))
        radio.click()
        driver.implicitly_wait(10)
    except:
        raise Exception("ERROR : Can't Select Hospital Type")
        
        
# Click on <DISTRICT_NAME> district and load the pages
def select_district_and_wait_until_load(driver,wait,district_name):
    try:
        driver.find_element_by_xpath("//select[@name='ctl00$ContentPlaceHolder1$ddl_District']/option[text()='{}']".format(district_name)).click()
        while still_loading(driver,wait) != "none":
            driver.implicitly_wait(2)
        driver.implicitly_wait(10)
        wait.until(EC.element_to_be_clickable((By.ID,"ctl00_ContentPlaceHolder1_GridView2")))
    except:
        raise Exception("ERROR : Can't select district")
        

# Get no of pages (Pagination) for selected district
def no_of_pages_for_selected_district_and_type(driver):
    try:
        pages=len(driver.find_elements_by_xpath("//*[@id='ctl00_ContentPlaceHolder1_GridView2']/tbody/tr[1]/td/table/tbody/tr/td"))
        if pages == 0:
            pages = 1
        return pages
    except:
        raise Exception("ERROR : Can't get number of pages for selected district and type")
        
# Select page
def select_page_pagination_section(driver,page_no):
    try:
        driver.find_element_by_xpath("//*[@id='ctl00_ContentPlaceHolder1_GridView2']/tbody/tr[1]/td/table/tbody/tr/td[{}]/a".format(str(page_no))).click()
        while still_loading(driver,wait) != "none":
            driver.implicitly_wait(2)
        driver.implicitly_wait(2)
        wait.until(EC.element_to_be_clickable((By.ID,"ctl00_ContentPlaceHolder1_GridView2")))
    except:
        raise Exception("ERROR : Switching page for pagination")
        
        
# Click on all the "View Detailed break up option"
def toggle_detailed_break_up_section(driver):
    try:
        driver.find_element_by_xpath("//*[contains(@id,'_div_card')]/div[2]/div[2]/div[1]/a").click()
        driver.implicitly_wait(5)
    except:
        raise Exception("ERROR : Can't open detailed break up section")

        
def MobileCleanData(data):
    # Process data for DB
    # Database only have Big Integer field , String not accepted
    result = []
    copydata = None
    # Split data at "/" & "," for multiple mobile number
    if "/" in str(data):
        copydata = str(data).split("/")
    elif "," in str(data):
        copydata = str(data).split(",")
    else:
        copydata = [data]

    for item in copydata:
        try:
            # Remove "+"
            # Remove "(" & ")"
            # Remove "-"
            # Remove all blank spaces
            tmp = item.replace("+","").replace("(","").replace(")","").replace("-","").replace(" ","") 
            
            # Check whether its is empty or not before typecasting to int to reduce possibility of error
            if tmp.strip() != "":
                result.append(int(tmp))
        
        except ValueError:
            print(f"{item} failed")
    # Will return a tupple of (<No of mobile numbers>, [list of <mobileno>])
    return len(result),result


scraping  = False

# Main Driver function for scraping
def scrape_data(driver):
    scraping = True

    # Get the list of hospotals entry
    entries = driver.find_elements_by_xpath("//*[contains(@id,'_div_card')]")
    
    if len(entries) == 0 :
        print("No items found")
        scraping = False
        return
    
    toggle_detailed_break_up_section(driver)

    
    # No of hospitals under selected category and dsitrct
    print(str(len(entries)) + " items fetched.")

    # Iterate through the entried and print the details
    for ei,e in enumerate(entries):
        
    #     print(ei)
        print("Name : {}".format(e.find_element_by_xpath(".//h5").text))
        print("Address : {}".format(e.find_element_by_xpath("(.//div/div/div)[1]").text))
        print("Phoneno : {}".format(MobileCleanData(e.find_element_by_xpath("(.//div/div/div)[2]//a").text)[1][0]))
        print("Total Beds : {}".format(e.find_element_by_xpath(".//div[2]/div[1]/div[4]/div/ul/li[1]/h3").text))
        print("Available Beds : {}".format(e.find_element_by_xpath(".//div[2]/div[1]/div[4]/div/ul/li[2]/h3").text))
        print("Verified On : {}".format(e.find_element_by_xpath(".//div[3]/small").text))
        print("------------------------")
        bed_categories = e.find_elements_by_xpath(".//div[2]/div[2]/div[2]/div/div")
        print("Categories of beds : {}".format(len(bed_categories)))
        for bc in bed_categories:
            # Make sure you have click on "View detailed Details" else you will get blank details
            try:
                print("Category : {}".format(bc.find_element_by_xpath(".//div/div[1]").text))
                print("Available : {}".format(bc.find_element_by_xpath(".//div/div[2]/div/div[4]/div/ul/li[2]/h3").text))
                print("Total : {}".format(bc.find_element_by_xpath(".//div/div[2]/div/div[4]/div/ul/li[1]/h3").text))
            except:
                print("Due to error skipping the category section")
            print("----category_ end-------\n")
            
        print("----------END------------")
    scraping = False

def still_loading(driver,wait):
    try:
        return driver.find_element_by_xpath('//*[@id="ctl00_ContentPlaceHolder1_upPgo"]').value_of_css_property("display")
    except:
        return "error"
    


driver,wait = init_scrape(chrome_options,endpoint)
for district_lable,district_id in using_district_list.items():
#     print(district_lable,district_id)
    for hospital_type in using_hospital_type:
        select_hospital_type(driver,using_hospital_type[hospital_type]["webkey"])
        select_district_and_wait_until_load(driver,wait,district_lable)
        time.sleep(5)
        no_of_pages = no_of_pages_for_selected_district_and_type(driver)
        global_buggy_pnum = 0
        for pg_no in range(no_of_pages):
            if pg_no != 0 or (pg_no==0 and global_buggy_pnum!=0) :
                while True:
                    if scraping:
                        time.sleep(2)
                    else:
                        global_buggy_pnum = pg_no
                        select_page_pagination_section(driver,pg_no+1)
                        time.sleep(10)
                        break
            
            while still_loading(driver,wait) != "none":
                driver.implicitly_wait(10)
            scrape_data(driver)
        print(f"Exiting from District : {district_lable} Type : {hospital_type} Page No : {pg_no}")

