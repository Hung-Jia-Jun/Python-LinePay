from django.shortcuts import render
from django.http import HttpResponse
from linebot import LineBotApi
from linebot.exceptions import *
from django.views.decorators.csrf import csrf_exempt
from linebot import *
import pdb
from linebot.models import *
from LinepayAPP.classLib import *
from LinepayAPP.models import *
import LinepayAPP.CarouselTemplateGenerator as CarouselTemplateGenerator
import json
import os
import LinepayAPP.fetchWebServiceData as fetchWebServiceData


if os.environ.get('isHeroku') == 'true':
    channelAccessToken = os.environ.get('channelAccessToken')
    channelSecret = os.environ.get('channelSecret')
else:
    channelAccessToken = 'XNE8bmST6IvwcucMwcc04BpW1Elj5PfdrO4c3LWHck+6/ajJj3GkwsbCHFKf9bZoMdZTpGWLFgHw9ThHNk7iK33xZkR6+QalKa5qOCaqi5JrLa6R8Madhr98iBStVZxnd19+ZbrBhPeZkyQI26xSmgdB04t89/1O/w1cDnyilFU='
    channelSecret = '4cd68a056f75e966b7e05d21fc9990db'

line_bot_api = LineBotApi(channelAccessToken)
handler = WebhookHandler(channelSecret)

def isMember(lineID):
    memberInfo = member.objects.filter(lineID=lineID).first()
    if memberInfo == None:
        return False
    else:
        return True


class memberAction:
    def __init__(self,lineID ,displayName):
        self.lineID = lineID
        self.displayName = displayName
    
    def createSession(self):
        member = self.getMember()
        if member == None:
            member = self.createMember()
        ClientSession = clientSession(member = member)
        ClientSession.save()
        return ClientSession

    def updateSession(self,status):
        memberInfo = clientSession.objects.filter(member__lineID=self.lineID).first()
        memberInfo.status = status
        memberInfo.save()
        return memberInfo

    def getSession(self):
        memberInfo = clientSession.objects.filter(member__lineID=self.lineID).first()
        return memberInfo

    def createMember(self):
        Member = member(displayName = self.displayName,lineID = self.lineID)
        Member.save()
        return Member

    def saveMemberPhone(self,ClientMsg):
        Member = member.objects.filter(lineID=self.lineID).first()
        Member.phone = ClientMsg
        Member.save()
        return Member

    def saveMemberBirth(self,birthDay):
        Member = member.objects.filter(lineID=self.lineID).first()
        Member.birthDay = birthDay
        Member.save()
        return Member

    def getMember(self):
        Member = member.objects.filter(lineID=self.lineID).first()
        return Member

    def normalMember(self,id = None):
        return None
class Product:
    def __init__(self,pdtPicture):
        if pdtPicture != '':
            self.pdtPicture = 'https://i.imgur.com/we4ZGlS.jpg'#'https://i.imgur.com/WNHByu2.png'#pdtPicture.replace('\\\\','\\').replace('\\','/').split(':')[1][1:]
        else:
            self.pdtPicture = 'https://i.imgur.com/we4ZGlS.jpg'
    
def addCart(lineID,shopID,pdtProductName,pdtPrice):
    memberInfo = clientSession.objects.filter(member__lineID=lineID).first()
    Cart = shoppingCart(member = memberInfo.member , 
                        shopId = shopID , 
                        itemName = pdtProductName,
                        itemPrice = pdtPrice)
    Cart.save()
    return Cart
class lineMessage:
    def __init__(self,to):
        self.to = to

    def textMessage(self,message):
        referenceMessage = line_bot_api.push_message(self.to, TextSendMessage(text=message))
        return referenceMessage

    def getDataConfirm(self):
        path = os.getcwd()+'\\LinepayAPP\\資料確認.json'
        with open(path, 'r') as reader:
            DataConfirm = json.loads(reader.read())
        return DataConfirm
    
    def orderInfoFlex(self,lineID,displayName,phone,address):
        DataConfirm = self.getDataConfirm()
        DataConfirm['body']['contents'][0]['text'] = '購物車'
        content = DataConfirm['body']['contents'][2]['contents']
        splitLine = DataConfirm['body']['contents'][1]
        buyItemCol = DataConfirm['body']['contents'][2]['contents'][0]
        content[0]['contents'][1]['text'] = displayName
        content[1]['contents'][1]['text'] = phone    
        content[2]['contents'][0]['text'] = '送餐地址'
        content[2]['contents'][1]['text'] = address
        orders = shoppingCart.objects.filter(member__lineID = lineID)
        
        #創建購物車介面
        orderTotalElement = len(orders)
        contentTotalElement = len(content)

        
        transforToStringBuyItemCol = json.dumps(buyItemCol)
        rebackToJsonObjectBuyItemCol = json.loads(transforToStringBuyItemCol)
        buyItemCol = rebackToJsonObjectBuyItemCol

        content.append(splitLine)
        for i in range(orderTotalElement):
            content.append(buyItemCol)
            Price = str(orders[i].itemPrice)
            content[len(content)-1]['contents'][0]['text'] = orders[i].itemName
            content[len(content)-1]['contents'][1]['text'] = Price
            
            addOnNames = orders[i].addOnNameHistory.split(',')
            addOnPrices = orders[i].addOnPriceHistory.split(',')
            # for j in range(len(addOnNames)):
            #     content[j]['contents'][0] = addOnNames[j]
            #     content[j]['contents'][1] = addOnPrices[j]

        message = FlexSendMessage(alt_text="購物車資訊", contents=DataConfirm)
        response = line_bot_api.push_message(self.to, message)
        return response , content

    def memberInfoFlex(self,displayName,phone,birthday):
        DataConfirm = getDataConfirm()
        content = DataConfirm['body']['contents'][2]['contents']

        content[0]['contents'][1]['text'] = displayName
        content[1]['contents'][1]['text'] = phone    
        content[2]['contents'][1]['text'] = birthday

        message = FlexSendMessage(alt_text="資料確認", contents=DataConfirm)
        line_bot_api.push_message(self.to, message)
        return message

    def datetimePicker(self):
        date_picker = TemplateSendMessage(
                alt_text='請選擇生日',
                template=ButtonsTemplate(
                    text='請選擇生日',
                    actions=[
                        DatetimePickerTemplateAction(
                            label='選擇',
                            data='action=buy&itemid=1',
                            mode='date',
                            initial='1900-01-01',
                            max='2099-12-31'
                        )
                    ]
                )
            )
        line_bot_api.push_message(self.to, date_picker)
        return date_picker

    
@csrf_exempt
def callback(request):
    messageCallback = request.body
    decodeToText = decodeJson(messageCallback)
    lineEvent = decodeToText.parse()
    lineEvent = lineEvent.events[0]

    lineID = lineEvent.source.userId
    profile = line_bot_api.get_profile(lineID)
    Display_name = profile.display_name
    MemberAction = memberAction(lineID = lineID,displayName = Display_name)
    member = MemberAction.getMember()
    classNahoo = fetchWebServiceData.nahoo()
    switch = {
            '註冊-電話號碼': MemberAction.saveMemberPhone,
            '註冊-生日' : MemberAction.saveMemberBirth,
            
            #無用的跳出函式 MemberAction.normalMember
            '正常用戶' : MemberAction.normalMember,
            '正常用戶-已選擇店點' : classNahoo.returnWebMenuData,
            '正常用戶-已選擇商品' : MemberAction.normalMember,
             }
    
    selectShopId = "0"
    case = MemberAction.getSession()
    carouselTemplateMSG = CarouselTemplateGenerator.Generator()
    
    if lineEvent.type != 'postback':
        ClientMsg = lineEvent.message.text
    elif case != None and case.status == '正常用戶':
        ClientMsg = lineEvent.postback.data
    elif case != None and case.status == '正常用戶-已選擇店點':
        ClientMsg = lineEvent.postback.data
    elif case != None and case.status == '正常用戶-已選擇商品':
        ClientMsg = lineEvent.postback.data
    elif case != None and case.status == '正常用戶-加料中':
        ClientMsg = lineEvent.postback.data
    else:
        ClientMsg = lineEvent.postback.params.date

    LineMessage = lineMessage(lineID)
    if ClientMsg == "點餐":
        MemberAction.createSession()
        MemberAction.updateSession('正常用戶')
        

    if ClientMsg == '購物車清單':
        if member.address =='':
            LineMessage.textMessage('請輸入送餐地址')
            MemberAction.updateSession('註冊-地址')
            return HttpResponse()
        LineMessage.orderInfoFlex(lineID,Display_name,member.phone,member.address)
       
    if ClientMsg == "加料完畢":
        MemberAction.updateSession('正常用戶-詢問是否繼續訂餐')

    if isMember(lineID) == False:
        LineMessage.textMessage("您尚未註冊會員 \
                                    請輸入您的電話號碼註冊會員 \
                                    範例:09xxxxxxxx")
        MemberAction.createSession()
        MemberAction.updateSession('註冊-電話號碼')
    
    case = MemberAction.getSession()

    MessageActions = []
    carouselItems = []
    carouselItems = []
    if case != None:
        try:
            reciveData = switch[case.status](ClientMsg)
        except:
            pass
        if case.status == '正常用戶-檢查繼續訂餐':
            if ClientMsg == '是':
                #輸出店家列表
                case.status = '正常用戶'
            if ClientMsg == '否':
                if member.address =='':
                    LineMessage.textMessage('請輸入送餐地址')
                    MemberAction.updateSession('註冊-地址')
                    return HttpResponse()
                else:
                    LineMessage.orderInfoFlex(lineID,Display_name,member.phone,member.address)
        if case.status == '註冊-電話號碼':
            LineMessage.datetimePicker()
            MemberAction.updateSession('註冊-生日')

        if case.status == '註冊-地址':
            member.address = ClientMsg
            member.save()
            LineMessage.orderInfoFlex(lineID,Display_name,member.phone,member.address)
        
        if case.status == '註冊-生日':
            LineMessage.memberInfoFlex(member.displayName,member.phone,member.birthDay)
            LineMessage.textMessage('您好'+member.displayName+',您已註冊成功')
            MemberAction.updateSession('正常用戶')
        
        if case.status == '正常用戶':
            HqIds = classNahoo.queryHqInfoIds()
            shopList = []
            for hq in HqIds:
                for shop in classNahoo.queryShopIds(hq):
                    shopList.append(shop)
                        
            for shop in shopList:
                MessageActions = []
                _shopInfo = classNahoo.shopInfo(shop)
                if _shopInfo == None:
                    continue
                shpAddress = _shopInfo["shpAddress"]
                shpShopName = _shopInfo["shpShopName"]
                imageUrl = 'https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_5_carousel.png'
                MessageActions.append(carouselTemplateMSG.PostbackAction(label = '選擇該店訂餐',
                                                                text = None,
                                                                data = str(shop),
                                                                    ))
                                                                
                carouselItems.append(carouselTemplateMSG.carouselItem(thumbnail_image_url = imageUrl,
                                                                title = shpShopName,
                                                                text = shpAddress,
                                                                action = MessageActions))
            carouselTemplateObjs = carouselTemplateMSG.carouselTemplate(alt_text = '店鋪列表',
                                                        CarouselList = carouselItems)
            for carouse in carouselTemplateObjs:
                line_bot_api.push_message(LineMessage.to, carouse)
            MemberAction.updateSession('正常用戶-已選擇店點')
            
        if case.status == '正常用戶-已選擇店點':
            menu = reciveData
            if menu == '該店沒有菜單':
                LineMessage.textMessage(menu)
                return HttpResponse()
            for product in menu["products"]:
                MessageActions = []
                pdtProductName = product['pdtProductName']
                pdtPrice = str(product['pdtPrice'])
                product = Product(product["pdtPicturePath"])
                
                shopID = ClientMsg
                MessageActions.append(carouselTemplateMSG.PostbackAction(label = pdtProductName[0:20],
                                                                        text = None,
                                                                        data = shopID +","+pdtProductName[0:20]+","+pdtPrice,
                                                                        ))
                                                                
                carouselItems.append(carouselTemplateMSG.carouselItem(thumbnail_image_url = product.pdtPicture,
                                                                title = pdtProductName[0:20],
                                                                text = pdtPrice,
                                                            action = MessageActions))
               
            carouselTemplateObjs = carouselTemplateMSG.carouselTemplate(alt_text = '菜單',
                                                         CarouselList = carouselItems)
            
            for carouse in carouselTemplateObjs:
                line_bot_api.push_message(LineMessage.to, carouse)
            MemberAction.updateSession('正常用戶-已選擇商品')
            return HttpResponse()
        
        if case.status == '正常用戶-已選擇商品':
            LineMessage.textMessage('請問要加什麼料呢?')
            shopID , pdtProductName , pdtPrice= ClientMsg.split(',')
            
            addCart(lineID,shopID,pdtProductName,pdtPrice)           
            
            productsAdds = classNahoo.returnAddonItem(shopId = shopID , productName = pdtProductName)
            for item in productsAdds:
                MessageActions = []
                name = item['name']
                price = str(item['price'])
                pdtPicturePath = item['picturePath']
                product = Product(pdtPicturePath)
           
                MessageActions.append(carouselTemplateMSG.PostbackAction(label = name,
                                                                        text = None,
                                                                        data = pdtProductName +","+name+","+price,
                                                                        ))
                MessageActions.append(carouselTemplateMSG.MessageAction(label = '加料完畢',
                                                                        text = '加料完畢'))                                      

                carouselItems.append(carouselTemplateMSG.carouselItem(thumbnail_image_url = product.pdtPicture,
                                                                title = name,
                                                                text = '價格 :' + price,
                                                            action = MessageActions))
               
            carouselTemplateObjs = carouselTemplateMSG.carouselTemplate(alt_text = '加料選擇',
                                                         CarouselList = carouselItems)
            
            for carouse in carouselTemplateObjs:
                line_bot_api.push_message(LineMessage.to, carouse)
            MemberAction.updateSession('正常用戶-加料中')
        
        if case.status == '正常用戶-加料中':
            pdtProductName , name , price= ClientMsg.split(',')
            LineMessage.textMessage(pdtProductName + '加' + name + '。如果不再加料請按加料完畢')
            order = shoppingCart.objects.filter(member__lineID = lineID ,  
                                        itemName = pdtProductName).first()
            order.addOnNameHistory += ','+ name
            order.addOnPriceHistory += ','+ price
            order.save()

        if case.status == '正常用戶-詢問是否繼續訂餐':
            MessageActions = []
            carouselItems = []
            MessageActions.append(carouselTemplateMSG.MessageAction(label = '是',
                                                                        text = '是',
                                                                        ))
            MessageActions.append(carouselTemplateMSG.MessageAction(label = '否',
                                                                        text = '否',
                                                                        ))

            carouselTemplateObj = TemplateSendMessage(
                                    alt_text='是否繼續點餐?',
                                    template=ConfirmTemplate(
                                        text='是否繼續點餐?',
                                                actions=[
                                                    MessageAction(
                                                        label='是', text='是'
                                                    ),
                                                    MessageAction(
                                                        label='否', text='否'
                                                    )
                                                ]
                                            )
                                        )              
            line_bot_api.push_message(LineMessage.to, carouselTemplateObj)
            MemberAction.updateSession('正常用戶-檢查繼續訂餐')

        
    return HttpResponse()


#付款狀態確認
def confirm(request):
    transactionId = request.GET["transactionId"]
    orderId = request.GET["orderId"]
    print (transactionId)
    print (orderId)
    return HttpResponse("OK")
