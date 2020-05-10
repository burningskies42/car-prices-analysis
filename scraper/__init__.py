import requests
import urllib.request
import time
import datetime
from bs4 import BeautifulSoup
import re
import pandas as pd

class carProperties(object):
    def __init__(self, url, verbose = False):
        self.url = url
        self.verbose = verbose
        self._soup = None
        self.title = None

        self.overview_dict = dict()
        self.consupmtion_attributes_dict = dict()
        self.equipment_list = list()
        self.data = dict()

        self._brands = {'Audi', 'Mini (BMW) ', 'Mitsubishi', 'Smart', 'Volkswagen'}
        self._models = {'Club','A1','A3','A4','A5','A6',
            'Asx','Beetle','Caddy','Fortwo','Golf','Passat',
            'Polo','Q2','Q3','Q5','Sharan','T-Cross','T-Roc','T6','Tiguan','Touran','Tt','Up!'}

        self._attrib_dict = {'Hubraum':'motor_size',
'Vorbesitzer':'prev_owners',
'Türen':'doors',
'Sitze':'seats'}

        self._equipment_list = set(['Reifendruckkontrolle','Einparkhilfe','Einparkhilfe hinten','Tagfahrlicht','Start-/Stop-Automatik','ISOFIX vorbereitet','Sitzheizung','Leichtmetallfelgen','Kopfairbag','MP3','Mittelarmlehne','Freisprechanlage','Bluetooth','Handyvorbereitung','USB-Schnittstelle','Multifunktionslenkrad','umklappbare Rückksitzbank','Lichtassistent','Navigation','Klimaautomatik','Einparkhilfe vorne','Regenassistent','CD-Player','Geschwindigkeitsassist.','Scheinwerferreinigung','Partikelfilter','metallic Lackierung','Servotronic','Lendenwirbelstütze','LED Heckleuchten','Katalysator','Sportsitze','Kurvenlicht','Berganfahrassistent','Dachreling','Nebelleuchten','getönte Scheiben','Xenon','elektr. Differentialsperre','Telefon','LED Scheinwerfer','Fernlichtassistent','Abstandsassistent','Sportpaket','Komfortschlüssel','Sportfahrwerk','el. Heckklappe','Sprachsteuerung','Spurhalteassistent','Anhängerkupplung','Einparkkamery','variabler Ladeboden','Parkassistent','Spurwechselassistent','Schiebedach','Panoramadach','Alarmanlage','el. Sitze','Standheizung','Sonnenschutzrollo','dritte Sitzreihe','Head-Up-Display'])

        self.parse()
        self.build()

    def parse(self):
        response = requests.get(self.url)
        self._soup = BeautifulSoup(response.text, 'html.parser')

    def get_title(self):
        self.title = self._soup.findAll('h1')[0].text

    def get_brand(self):
        for b in self._brands:
            if b.lower() in self.title.lower():
                self.data['brand'] = b 
                break

    def get_model(self):
        for m in self._models:
            if m.lower() in self.title.lower():
                self.data['model'] = m
                break

    def get_price(self):
        price = self._soup.body.findAll(text='Preis')[0].parent.parent.findAll('p')[1].text
        self.data['price'] = int(re.sub(r'[^0-9]','',price))

    def get_overview(self):
        self.overview_dict = {l.findChild('dt').text.replace(':','') :l.findChild('dd').text for l in self._soup.findAll('dl')}

        # extract properties
        try:
            mnth,year = self.overview_dict['Erstzulassung'].split('.')
            self.data['age'] = (datetime.datetime.today().year - int(year))*12 + datetime.datetime.today().month - int(mnth) 
        except:
            self.data['age'] = None

        self.data['power'] = re.search(r'\((\d+).*\)',self.overview_dict['Leistung'])[1]
        self.data['engine'] = int(re.sub(r'[^0-9]','',self.overview_dict['Hubraum']))
        self.data['automatic_transmission']= self.overview_dict['Getriebe'].lower() == 'automatik'
        self.data['guarantee']= self.overview_dict['Garantie'].lower() == 'ja'

        for k,v in self._attrib_dict.items():
            try:
                self.data[v] =  int(re.sub(r'[^0-9]','',self.overview_dict[k])) 
            except:
                self.data[v] = None

    def get_consumption(self):
        consupmtion_attributes_list =[
            'Verbrauch außerorts', 'Verbrauch kombiniert', 'Zugrunde liegende Treibstoffart',
            'CO2-Emissionen', 'Umweltplakette', 'Abgasnorm', 'Jahressteuer']

        self.consupmtion_attributes_dict=dict()

        for k in consupmtion_attributes_list:
            try:
                self.consupmtion_attributes_dict[k] = self._soup.body.findAll(text=k)[0].parent.parent.findAll('div')[1].text
            except:
                if self.verbose:
                    print(f'Attribute {k} not found')

        self.data['consumption'] = int(re.sub(r'[^0-9]','',self.consupmtion_attributes_dict['Verbrauch kombiniert'].split('/')[0]))

    def get_equipment(self):
        equipment = [l.strip() for l in self._soup.findAll("div", {"class": "container-equipment"})[0].text.split('\n') if len(l)>1]
        for k in self._equipment_list:
            self.data[k] = k in equipment


    def get_data(self):
        se = pd.Series(self.data)
        se.name = self.overview_dict['Interne Nummer']
        return se

    def build(self):
        self.get_title()
        self.get_brand()
        self.get_model()
        self.get_price()

        self.get_overview()
        self.get_consumption()

        self.get_equipment()

        self.data.columns = [re.sub(r'[^a-z0-9]','',c.lower().replace(' ','_')) for c in self.data.columns]
