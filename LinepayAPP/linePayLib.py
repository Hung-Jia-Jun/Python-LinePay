import requests
import json
import pdb
import configparser
from datetime import datetime
class linePay:
    def __init__(self):
        self.baseUrl = "https://api-pay.line.me/v2/payments"
        self.channelId,self.channelSecret = self.readLinePayID()
        self.confirmUrl = "https://www.nahoo.com.tw/Line.php"
        self.headers = {"Content-Type": "application/json;charset=UTF-8",
                    "X-LINE-ChannelId":self.channelId,
                    "X-LINE-ChannelSecret":self.channelSecret}
        self.reserveUrl = self.baseUrl + "/request"
        self.orderId = ""

    def reserveOrder(self, productName, amount, productImageUrl):
        self.productName = productName
        self.amount = amount
        import pdb
        pdb.set_trace()
        data ={"productName":productName,
               "productImageUrl": productImageUrl,
                "amount":self.amount,
                "currency":"TWD",
                "confirmUrl": self.confirmUrl+"?orderId="+self.orderId,
                "orderId":self.orderId}
                
        # "confirmUrl": self.confirmUrl+"/confirm/?orderId="+self.orderId,
                        
        self.paymentResponse = requests.post(self.reserveUrl, headers=self.headers, json=data)
        
        self.getPaymentURL()

    def confirmPayment(self,transactionId,amount):
        self.amount = amount
        confirmURL = self.baseUrl + "/" + str(transactionId) + "/confirm"
        data = {"amount": amount, "currency": "TWD"}
        self.paymentResponse = requests.post(confirmURL, headers=self.headers, json=data)
        return self.paymentResponse

    def getPaymentURL(self):
        _paymentJson = json.loads(self.paymentResponse.text)
        self.paymentURL = _paymentJson["info"]["paymentUrl"]["web"]
        self.transactionId = _paymentJson["info"]["transactionId"]

    def readLinePayID(self):
        config = configparser.ConfigParser()
        # config.read("config.ini")
        config.read("/home/nahoo/LinePay/pos-bot/config.ini")
        _channelId = config["LinePayID"]["ChannelId"]
        _channelSecret = config["LinePayID"]["ChannelSecret"]
        return _channelId,_channelSecret
if __name__ == "__main__":
    linePay = linePay()
    
    now = datetime.now()

    #設定訂單編號
    linePay.orderId = now.strftime("%Y%m%d%H%M%S")

    productName = "Test123"
    amount = "1"

    productImageUrl = "https://i.imgur.com/vf0ngTg.jpg"
    linePay.reserveOrder(productName, amount, productImageUrl)
    
    print("paymentURL:" + linePay.paymentURL)
    print("transactionId:" + str(linePay.transactionId))

    #transactionId = 2020040500507514210
    #response = linePay.confirmPayment(transactionId, amount)
    #print(response.text)
