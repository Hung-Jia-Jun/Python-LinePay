import requests
import json
import pdb
import configparser

class linePay:
    def __init__(self):
        self.baseUrl = "https://sandbox-api-pay.line.me/v2/payments"
        self.channelId,self.channelSecret = self.readLinePayID()
        self.confirmUrl = ""
        self.headers = {"Content-Type": "application/json",
                    "X-LINE-ChannelId":self.channelId,
                    "X-LINE-ChannelSecret":self.channelSecret}
        self.reserveUrl = self.baseUrl + "/request"
        self.orderId = ""
    def reserveOrder(self,productName,amount):
        self.productName = productName
        self.amount = amount
        data ={"productName":productName,
                "productImageUrl":"https://imgur.com/gallery/NaGrZUz",
                "amount":self.amount,
                "currency":"TWD",
                "confirmUrl": self.confirmUrl+"/confirm/?orderId="+self.orderId,
                "orderId":self.orderId}
                        
        self.paymentResponse = requests.post(self.reserveUrl, headers=self.headers, json=data)
        
        self.getPaymentURL()

    def getPaymentURL(self):
        _paymentJson = json.loads(self.paymentResponse.text)
        self.paymentURL = _paymentJson["info"]["paymentUrl"]["web"]
        self.transactionId = _paymentJson["info"]["transactionId"]

    def readLinePayID(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        _channelId = config["LinePayID"]["ChannelId"]
        _channelSecret = config["LinePayID"]["ChannelSecret"]
        return _channelId,_channelSecret
if __name__ == "__main__":
    linePay = linePay()
    
    """
    productName = "Test123"
    amount = "1000"

    linePay.reserveOrder(productName,amount)
    
    print(linePay.paymentURL)
    print(linePay.transactionId)
    """