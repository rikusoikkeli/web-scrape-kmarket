# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 10:55:06 2020

@author: rikus
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
import datetime
import os.path # recommended method for joining one or more path components
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
chromedriver_path = "C:\Omat tiedostot\Koodihommat\Misc\harjoitustyöt\selenium_project\chromedriver_win32\chromedriver.exe"
current_file_path = os.path.dirname(__file__)


class WebScrape(object):
    
    def __init__(self, chromedriver_path, current_file_path):
        self.chromedriver_path = chromedriver_path
        self.current_file_path = current_file_path
        
        # Tallentaa Selenium käyttäjädatan ohjelman kotikansioon, jotta ei tarvitse
        # aina vastata uudestaan ilmoituksiin.
        self.chrome_options = Options()
        self.chrome_options.add_argument("user-data-dir=selenium_user_data") 
        self.driver = webdriver.Chrome(self.chromedriver_path, options=self.chrome_options)
        self.driver.implicitly_wait(5)
        
        self.all_categories_page = "https://www.k-ruoka.fi/kauppa/tuotteet"
        self.category_dict = {}
        self.all_items_dict = {}
        
    
    def getCategoryDict(self):
        """
        category_dict: Yhden tuotekategorian sisältämät tiedot (dict)
        """
        return self.category_dict
    
    
    def getAllItemsDict(self):
        """
        all_items_dict: Kaikkien tuotekategorioiden sisältämät tiedot (dict)
        """
        return self.all_items_dict


    def goToAllCategories(self):
        """
        Vie Tuotteet-sivulle, josta löytyy kaikki tuotekategoriat.
        """
        self.driver.get(self.all_categories_page)


    def downloadItems(self):
        """
        Noutaa sivun tuotteiden tiedot ja kerää ne dictiin muodossa:
            item_number : (item_name, item_price)
        """
        # jokainen tuote löytyy html-luokasta nimeltä "bundle-list-item"
        items_selenium = self.driver.find_elements_by_class_name("bundle-list-item")
        # iteroidaan kaikki tuotteet
        for item in items_selenium:
            # haetaan xpath-osoitteella tuotenumero
            # "." polun alussa tarkoittaa, että suoritetaan etsintä annetun html-luokan scopessa
            temp = item.find_element_by_xpath(".//div[contains(@id,'product-result')]")
            temp = temp.get_attribute("id")
            index = temp.find("item")
            item_number = temp[index+5:]
            item_list = item.text.split("\n")
            item_name = item_list[0]
            item_price = item_list[-1]
            try:
                # int(item_price[0]) palauttaa exceptionin, jos price on jotain muuta kuin numeroita
                if int(item_price[0]) and item_price[-3:] == "/kg":
                    self.category_dict[item_number] = (item_name, item_price[0:-3])
            except:
                pass


    def saveData(self):
        """
        Tallentaa all_items_dict sisällön CSV :nä levylle. Tiedosto nimetään
        tallennuspäivämäärän mukaan.
        """
        current_time = datetime.datetime.now()
        current_time = str(current_time)[0:-7]
        
        aList = []
        for key in self.all_items_dict:
            number = key
            name, price = self.all_items_dict[key]
            row = (current_time, number, name, price)
            aList.append(row)
            print(row)
        
        filename = current_time[0:-9] + "_food_data.csv"
        folder = "data"
        relative_path = os.path.join(folder, filename)
        absolute_path = os.path.normcase(os.path.join(self.current_file_path, relative_path))
        
        with open(absolute_path, "w") as f:
            csv_writer = csv.writer(f, delimiter=";")
            for row in aList:
                csv_writer.writerow(row)


    def loadAllItems(self):
        """
        Vierittää valitun tuotekategorian alas saakka, kunnes elementti "Lataa lisää"
        ei ole enää clickattava.
        """
        while True:
            try:
                show_all_path = '//*[text()="Lataa lisää"]'
                show_all = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, show_all_path))
                        )
                show_all.click()
            except StaleElementReferenceException:
                pass
            except:
                break


    def runWebScrape(self):
        """
        Kerää valitun K-kaupan kaikki tuotekategoriat läpi, lataa niiden tiedot,
        tallentaa muuttujaan all_items_dict (dict) ja lopuksi tallentaa dictin tiedot
        levylle, CSV-tiedostoon.
        """
        start_time = datetime.datetime.now()
        print("Web scrape alkaa...")
        
        # mennään aloitussivulle
        self.goToAllCategories()
        
        # haetaan kaikki tarjolla olevat kategoriat muuttujaan categories_children
        categories_parent = self.driver.find_element_by_class_name("ProductCategoriesDesktop__categories")
        categories_children = categories_parent.find_elements_by_class_name("ProductCategoriesDesktop__categories__category")
        categories_children = categories_children[1:] # leikataan pois "Suosittelemme"
        
        end_count = len(categories_children)
        # iteroidaan kategoriat
        for i in range(end_count):
            
            try:
                # haetaan kaikki tarjolla olevat kategoriat muuttujaan categories_children
                categories_parent = self.driver.find_element_by_class_name("ProductCategoriesDesktop__categories")
                categories_children = categories_parent.find_elements_by_class_name("ProductCategoriesDesktop__categories__category")
                categories_children = categories_children[1:] # leikataan pois "Suosittelemme"
                
                category = categories_children[i]
                
                print(f"Kategorioita jäljellä: {end_count - i}")
                print(f"Mennään kategoriaan: {category.text}")
                
                # valitaan kategoria
                category.click()
                # valitaan alakategoriat
                subcategories = self.driver.find_element_by_class_name("ProductCategoriesDesktop__sub-categories")
                # valitaan kaikki tuotteet
                show_all = subcategories.find_element_by_xpath('.//*[text()="Näytä kaikki"]')
                # clickataan auki kaikki tuotteet
                show_all.click()
                
                print("Ladataan kaikkia tuotteita sivulta...")
                self.loadAllItems()
                print("Valmis!")
                print("Tallennetaan tuotteet dictiin...")
                self.downloadItems()
                print("Valmis!\n")
                self.all_items_dict.update(self.category_dict)
                
                # mennään aloitussivulle
                self.goToAllCategories()
                
            except Exception as e:
                print(e)
        
        end_time = datetime.datetime.now()
        total_time = end_time - start_time
        print(f"Web scrape on valmis! Aikaa kului: {total_time}")
        
        
browser = WebScrape(chromedriver_path, current_file_path)
browser.runWebScrape()
browser.saveData()














































