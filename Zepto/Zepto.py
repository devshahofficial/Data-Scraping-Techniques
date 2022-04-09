import json
import requests
import pandas as pd


class ZeptoScraper:
    def __init__(self):

        self.headers = json.load(open("headers.json"))
        self.locationApiUrl = "https://api.zepto.co.in/api/v1/config/layout/"
        self.subApiUrl = "https://api.zepto.co.in/api/v2/inventory/catalogue/store-products/"
        self.storeApiUrl = "https://api.zepto.co.in/api/v1/inventory/catalogue/categories/"
        self._maxPages = 1000
        self.categoryDataFrames = {}

    def joinLocationApiUrl(self, latitude, longitude):
        return self.locationApiUrl + "?" + "latitude=" + latitude + "&" + "longitude=" + longitude + "&" + "page_type=HOME"

    def joinSubApiUrl(self, storeID, subcategoryID, pageNumber):
        return self.subApiUrl + "?" + "store_id=" + storeID + "&" + "subcategory_id=" + subcategoryID + "&" + "page_number=" + str(
            pageNumber)

    def joinStoreApiUrl(self, storeID):
        return self.storeApiUrl + "?" + "store_id=" + storeID

    def scrape(self, latitude, longitude):
        locationResponse = requests.get(self.joinLocationApiUrl(latitude=latitude, longitude=longitude),
                                        headers=self.headers).json()
        if locationResponse['storeServiceableResponse']['serviceable'] == True:
            storeID = locationResponse['storeServiceableResponse']['storeId']
        else:
            print('Not serviceable')
            return

        storeApi = self.joinStoreApiUrl(storeID=storeID)
        storeResponse = requests.get(storeApi, headers=self.headers)

        categories = []
        for item in storeResponse.json()["categories"]:
            for avail in item["availableSubcategories"]:
                if avail['name'] == 'All':
                    _id = avail['id']
            categories.append({'name': item['name'], 'id': _id})

        self.categoryDataFrames = {}

        for sub in categories:
            listOfItems = []
            for _i in range(self._maxPages):
                url = self.joinSubApiUrl(storeID=storeID, subcategoryID=sub["id"], pageNumber=_i + 1)
                response = requests.get(url, headers=self.headers)
                products = response.json()["storeProducts"]
                if response.status_code != 200:
                    failed = response
                    print("Failed : " + str(failed.json()))

                for item in products:
                    listOfItems.append({
                        "name": item["product"]["name"],
                        "mrp": item["mrp"],
                        "discountPercent": item["discountPercent"],
                        "availableQuantity": item["availableQuantity"],
                        "discountedSellingPrice": item["discountedSellingPrice"],
                        "weightInGms": item["productVariant"]["weightInGms"],
                        "outOfStock": item["outOfStock"],
                        "quantity": item["productVariant"]["quantity"]
                    })

                if response.json()["endOfList"]:
                    print("Done scraping : " + sub['name'])
                    self.categoryDataFrames[sub['name']] = pd.DataFrame(listOfItems)
                    break

    def dataWriter(self, fileName):
        with pd.ExcelWriter(fileName) as database:
            for key in self.categoryDataFrames.keys():
                self.categoryDataFrames[key].to_excel(database, sheet_name=key, index=False)


if __name__ == '__main__':
    scraper = ZeptoScraper()
    latitude = "19.117854591807152"
    longitude = "72.86313006654382"
    scraper.scrape(latitude=latitude, longitude=longitude)
    scraper.dataWriter(fileName="Andheri.xlsx")
