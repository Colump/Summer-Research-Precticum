# jt_testing; Selenium Testing module for Journeyti.me Application

# This module requires the installation of selenium libraries:
#   -> pip install selenium

import os, sys, csv
# This might seem unusual... but to make sure we can import modules from the
# folder where jt_gtfs_loader is installed (e.g. if called as an installed
# endpoint) - we always add the module directory to the python path. Endpoints
# can be called from any 'working directory' - but modules can only be imported
# from the python path etc..
jt_testing_module_dir = os.path.dirname(__file__)
sys.path.insert(0, jt_testing_module_dir)
from datetime import datetime
from jt_utils import load_credentials
import traceback

# For python testing without specifying chrome driver location:
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.ie.service import Service as IEService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.microsoft import IEDriverManager

def test_using_chrome():
    # (ALTERNATIVE TO BELOW: Add driver location to path - always only one driver at a time!)
    # Use install() to get the location used by the manager and pass it into service class
    # SYNTAX FOM SELENIUM SITE:  DELETE IF NOTE NEEDED....  service=Service(executable_path=ChromeDriverManager().install()))
    service = ChromeService(executable_path=ChromeDriverManager().install())

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://https://api.journeyti.me/documentation.html
    #There are a bunch of types of information about the browser you can request, including window handles, browser size / position, cookies, alerts, etc.")
    title = driver.title

#     Synchronizing the code with the current state of the browser is one of the biggest challenges with Selenium, and doing it well is an advanced topic.

# Essentially you want to make sure that the element is on the page before you attempt to locate it and the element is in an interactable state before you attempt to interact with it.

# An implicit wait is rarely the best solution, but it’s the easiest to demonstrate here, so we’ll use it as a placeholder.
    driver.implicitly_wait(0.5)

    #Find an element 
    search_box = driver.find_element(by=By.NAME, value="q")
    search_button = driver.find_element(by=By.NAME, value="btnK")

    #Take action on element
    search_box.send_keys("Selenium")
    search_button.click()

    # Request element information
    value = search_box.get_attribute("value")

    driver.quit()


def test_using_edge():
    service = EdgeService(executable_path=EdgeChromiumDriverManager().install())

    driver = webdriver.Edge(service=service)

    driver.quit()


def test_using_firefox():
    service = FirefoxService(executable_path=GeckoDriverManager().install())

    driver = webdriver.Firefox(service=service)

    driver.quit()


# @pytest.mark.skip(reason="only runs on Windows")
# def test_ie_session():
#     service = IEService(executable_path=IEDriverManager().install())

#     driver = webdriver.Ie(service=service)

#     driver.quit()

#===============================================================================
#===============================================================================
#===============================================================================

def main():
    """Run Selenium tests for the Journeyti.me application


    """
    start_time = datetime.now()

    print('JT_Testing: Start of test set (' + start_time.strftime('%Y-%m-%d %H:%M:%S') + ')')

    # print('\tLoading credentials.')
    # # Load our private credentials from a JSON file
    # credentials = load_credentials()
    # import_dir  = jt_testing_module_dir + "/import/"

    try:
        test_using_chrome()
    except:
        # if there is any problem, print the traceback
        print(traceback.format_exc())

    # (following returns a timedelta object)
    elapsedTime = datetime.now() - start_time
    
    # returns (minutes, seconds)
    #minutes = divmod(elapsedTime.seconds, 60) 
    minutes = divmod(elapsedTime.total_seconds(), 60) 
    print('Tests Complete! (Elapsed time:', minutes[0], 'minutes', minutes[1], 'seconds)\n')
    sys.exit()

if __name__ == '__main__':
    main()