# -*- coding: utf-8 -*-
import os
import json
import re
import pandas as pd
import scrapy


class AwardsSpider(scrapy.Spider):
    name = 'awards'

    def start_requests(self):
        df = pd.read_csv('./events_link.csv')
        urls = df['link'].tolist()
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_first_page)

    def parse_first_page(self, response):

        sidebar = response.xpath('//*[@id="sidebar"]/div[@class="aux-content-widget-2"]/span/script').get() 
        sidebar = re.findall(r"(?<='right-.-react\',).*?(?=\]\);\n)", sidebar)[0]
        sidebar = json.loads(sidebar)
        event_id, event_year, event_instance = self.extract_data_from_sidebar(sidebar)
        path_event = os.path.join('.', 'data',  event_id)
        path_data = os.path.join(path_event, event_year, event_instance)

        if not os.path.exists(path_data):
            os.makedirs(path_event)
        with open(f'{path_event}/event_history.json', 'w') as f:
            json.dump(sidebar, f)

        content = response.xpath('//*[@id="main"]/div/span/script/text()').get()
        content = re.findall(r"(?<='center-.-react',).*?(?=\]\);\n)", content)[0]
        content = json.loads(content)

        if not os.path.exists(path_data):
            os.makedirs(path_data)

        with open(f'{path_data}/data.json', 'w') as f: 
            json.dump(content, f)

        try:
            title = response.xpath('/html/body/div[2]/div/div[2]/div[3]/div/div[1]/div[1]/div[1]/h1/text()').get()
        except:
            title = None

        try:
            description = response.xpath('/html/body/div[2]/div/div[2]/div[3]/div/div[1]/div[1]/div[2]/text()').get()
        except:
            description = None

        metadata = {
            'title': title,
            'description': description
        }

        with open(f'{path_data}/event_metadata.json', 'w') as f:
            json.dump(metadata, f)

        event_editions = sidebar['eventHistoryWidgetModel']['eventEditions']
        if len(event_editions) > 1:
            for edition in event_editions[1:]:
                next_year = edition['year']
                n_next_instance = edition['instanceWithinYear']
                for next_instance_id in range(n_next_instance):
                    next_uri = f'https://www.imdb.com/event/{event_id}/{next_year}/{n_next_instance}'
                    yield response.follow(next_uri, self.parse)

    def parse(self, response):
        page = response.url.split("/")
        event_id = page[4]
        event_year = page[5]
        event_item = page[6]
        path_event = os.path.join('.', 'data',  event_id)
        path_data = os.path.join(path_event, event_year, event_item)

        content = response.xpath('//*[@id="main"]/div/span/script/text()').get()
        content = re.findall(r"(?<='center-.-react',).*?(?=\]\);\n)", content)[0]
        content = json.loads(content)

        if not os.path.exists(path_data):
            os.makedirs(path_data)

        with open(f'{path_data}/data.json', 'w') as f: 
            json.dump(content, f)

        try:
            title = response.xpath('/html/body/div[2]/div/div[2]/div[3]/div/div[1]/div[1]/div[1]/h1/text()').get()
        except:
            title = None

        try:
            description = response.xpath('/html/body/div[2]/div/div[2]/div[3]/div/div[1]/div[1]/div[2]/text()').get()
        except:
            description = None

        metadata = {
            'title': title,
            'description': description
        }

        with open(f'{path_data}/event_metadata.json', 'w') as f:
            json.dump(metadata, f)

        yield

    def extract_data_from_sidebar(self, sidebar):
        event_id = sidebar['eventHistoryWidgetModel']['eventId']
        event_editions = sidebar['eventHistoryWidgetModel']['eventEditions']
        last_edition = event_editions[0]
        event_year = str(last_edition['year'])
        event_instance = str(last_edition['instanceWithinYear'])
        return event_id, event_year, event_instance

