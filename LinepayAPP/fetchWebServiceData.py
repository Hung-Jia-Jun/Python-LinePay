import zeep
import json
import requests
class nahoo:
    def __init__(self):
        # requests.packages.urllib3.disable_warnings()
        # requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
        # self.wsdl = 'https://cloud.nahoopos.com/services/nahooWebservice?WSDL'
        self.wsdl = 'http://60.248.91.143/services/nahooWebservice?WSDL'
        self.client = zeep.Client(wsdl=self.wsdl)
    
    def shopInfo(self,id):
        shopInfo = self.client.service.shopInfo(id)
        shopInfo = json.loads(shopInfo)
        return shopInfo

    def queryHqInfoIds(self):
        allHqList = self.client.service.queryHqInfoIds()
        if allHqList != 'No Data':
            allHqList = json.loads(allHqList)
            return allHqList
        else:
            return []

    def queryShopIds(self,hqId):
        allShopList = self.client.service.queryShopIds(hqId)
        if allShopList != 'No Data':
            allShopList = json.loads(allShopList)
            return allShopList
        else:
            return []

    def returnWebMenuData(self,shopId):
        menu = self.client.service.returnWebMenuData(shopId)
        if menu == None:
            return '該店沒有菜單'
        elif menu == '沒有發現新菜單':
            return '該店沒有菜單'
        else:
            menu = json.loads(menu)
            return menu
    def returnAddonItem(self,shopId,productName):
        menu = self.client.service.returnWebMenuData(shopId)
        menu = json.loads(menu)
        productsAdds = menu['productsAdds']
        return productsAdds


if __name__ == "__main__":
    nahoo = nahoo()
    nahoo.shopInfo('13')
    nahoo.queryHqInfoIds()
