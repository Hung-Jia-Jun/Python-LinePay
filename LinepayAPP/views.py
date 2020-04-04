from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse,JsonResponse
from linebot import LineBotApi
from linebot.exceptions import *
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from linebot import *
import pdb
import uuid
from linebot.models import *
from LinepayAPP.linePayLib import linePay
from LinepayAPP.classLib import *
from LinepayAPP.models import *
import LinepayAPP.CarouselTemplateGenerator as CarouselTemplateGenerator
import json
import os
import LinepayAPP.fetchWebServiceData as fetchWebServiceData
import configparser
import re
import LinepayAPP.barCodeGenerator as barCodeGenerator
from django.conf import settings
import random

config = configparser.ConfigParser()
config.read('config.ini')
# config.read("/Users/Jason/Scripts/LinePay_20200305/LinePay/pos-bot/config.ini")

channelAccessToken = config['Shop']['channelAccessToken']
channelSecret = config['Shop']['channelSecret'] 

#複寫Line傳送的函式用於測試用
class line_bot_api(LineBotApi):
    def __init__(self,fuction):
        self.fuction = fuction

    def push_message(self, *param):
        to, messages = param
        if settings.TESTING:
            #在測試模式下，不會真的送出
            log = testLog.objects.create(message = messages)
        else:
            return self.fuction.push_message(to, messages)

    def get_profile(self, userID):
        return self.fuction.get_profile(userID)

line_bot_api = line_bot_api(LineBotApi(channelAccessToken))

#line_bot_api = LineBotApi(channelAccessToken)

handler = WebhookHandler(channelSecret)

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
        _inviteCode = uuid.uuid1().hex[5:9]
        Member = member.objects.create(displayName = self.displayName,lineID = self.lineID)
        self.saveUsedInviteCode(owner = Member,code = _inviteCode)
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

    def checkInviteCode(self,inviteCode):
        invite = inviteCodeManager.objects.filter(code=inviteCode)
        return invite

    def delInviteCodeOwner(self,inviteCode):
        invitedMember = inviteCodeManager.objects.filter(code=inviteCode).first()
        invitedMember.delete()

    def reGeneratorInviteCode(self, invitedMember):
        getPos = random.randint(5, 32)
        inviteCodeNumber = uuid.uuid1().hex[getPos-4:getPos]
        inviteCodeManager.objects.create(owner = invitedMember,code = inviteCodeNumber)

    def saveUsedInviteCode(self,owner,code):
        inviteCodeManager.objects.create(owner = owner,code = code)

class Product:
    def __init__(self,pdtPicture):
        if pdtPicture != '':
            self.pdtPicture = pdtPicture  # 'https://i.imgur.com/we4ZGlS.jpg'
        else:
            self.pdtPicture = 'https://i.imgur.com/we4ZGlS.jpg'#'https://i.imgur.com/WNHByu2.png'#pdtPicture.replace('\\\\','\\').replace('\\','/').split(':')[1][1:]
    
def addCart(lineID,shopID,pdtProductName,pdtPrice,productImage,itemClassName,itemClassId):
    memberInfo = clientSession.objects.filter(member__lineID=lineID).first()
    Cart = shoppingCart.objects.create(member = memberInfo.member , 
                        shopId = shopID , 
                        itemName = pdtProductName,
                        itemPrice = pdtPrice,
                        isTaked = False,
                        productImage = productImage,
                        itemClassName = itemClassName,
                        itemClassId = itemClassId,
                        )
    return Cart

def clearShoppingCart():
    #清空購物車
    shoppingCart.objects.all().delete()

class lineMessage:
    def __init__(self,to):
        self.to = to

    def textMessage(self,message):
        referenceMessage = line_bot_api.push_message(self.to, TextSendMessage(text=message))
        return referenceMessage

    def imageMessage(self,imageURL):
        referenceMessage = line_bot_api.push_message(self.to, ImageSendMessage(original_content_url=imageURL , preview_image_url = imageURL))
        return referenceMessage

    def getDataConfirm(self):
        path = os.getcwd()+'/LinepayAPP/DataConfirm.json'
        with open(path, 'r' ,encoding='utf-8') as reader:
            DataConfirm = json.loads(reader.read())
        return DataConfirm
    
    def clearReferenceJson(self,buyItemCol):
        transforToStringBuyItemCol = json.dumps(buyItemCol)
        rebackToJsonObjectBuyItemCol = json.loads(transforToStringBuyItemCol)
        buyItemCol = rebackToJsonObjectBuyItemCol
        return buyItemCol

    def orderInfoFlex(self, lineID, displayName, phone, address, isUseInviteCode = False,inviteCodeNumber = None):
        DataConfirm = self.getDataConfirm()
        DataConfirm['body']['contents'][0]['text'] = '購物車'
        content = DataConfirm['body']['contents'][2]['contents']
        splitLine = DataConfirm['body']['contents'][1]
        buyItemCol = DataConfirm['body']['contents'][2]['contents'][0]
        content[0]['contents'][1]['text'] = displayName
        content[1]['contents'][1]['text'] = phone    
        content[2]['contents'][0]['text'] = '地址'
        content[2]['contents'][1]['text'] = address

        shoppingCart.objects.filter(member__lineID = lineID , isPayed = 'False' , productAmount = 0).delete()
        orders = shoppingCart.objects.filter(
            member__lineID=lineID, isPayed='False', cashOnDelivery=False).order_by('updated_at')
       
        if len(orders)==0:
            response = line_bot_api.push_message(self.to, TextSendMessage(text="購物車內無商品"))
            return response

        #創建購物車介面
        orderTotalElement = len(orders)
        content.append(splitLine)
        totalPrice = 0
        totalAmount = 0
        storeName = ''
        if orderTotalElement == 0:
            return None
        shopId = orders[0].shopId
        _shopInfo = fetchWebServiceData.nahoo().shopInfo(shopId)
        storeName = _shopInfo["shpShopName"]
        DataConfirm['body']['contents'][0]['text'] += '   ' + storeName

        for i in range(orderTotalElement):
            if inviteCodeNumber != None:
                orders[i].inviteCode = inviteCodeNumber
                orders[i].save()
            buyItemCol = self.clearReferenceJson(buyItemCol)
            content.append(buyItemCol)

            Price = str(orders[i].itemPrice)
            

            content[len(content)-1]['contents'][0]['text'] = str(i+1)+"."+orders[i].itemName
            content[len(content)-1]['contents'][1]['text'] = Price
            
            addOnNames = orders[i].addOnNameHistory.split(',')
            addOnPrices = orders[i].addOnPriceHistory.split(',')
            
            addOnNames = addOnNames[1:]
            addOnPrices = addOnPrices[1:]

            thisOrderPrice = 0
            for j in range(len(addOnNames)):
                buyItemCol = self.clearReferenceJson(buyItemCol)
                content.append(buyItemCol)
                content[len(content)-1]['contents'][0]['text'] = '    ' + addOnNames[j]
                content[len(content)-1]['contents'][1]['text'] = '    ' + addOnPrices[j]
                thisOrderPrice +=  int(addOnPrices[j])
                
            AmountItemCol = self.clearReferenceJson(buyItemCol)
            content.append(AmountItemCol)
            content[len(content)-1]['contents'][0]['text'] = '    ' + '購買數量'
            content[len(content)-1]['contents'][1]['text'] = '    ' + str(orders[i].productAmount)
                
            totalPrice += orders[i].productAmount* (int(Price) + thisOrderPrice)
            totalAmount += orders[i].productAmount
            content.append(splitLine)

        
        buyItemCol = self.clearReferenceJson(buyItemCol)
        content.append(buyItemCol)
        content[len(content)-1]['contents'][0]['text'] = '總數量'
        content[len(content)-1]['contents'][1]['text'] = str(totalAmount)

        if totalAmount == 0:
            DataConfirm['body']['contents'][0]['text'] = '購物車'
        if isUseInviteCode:
            setting = systemSetting.objects.all().first()
            saleNumber = setting.saleNumber
            salePrice = int(totalPrice) - round(totalPrice*(saleNumber/10))
            totalPrice = totalPrice - salePrice

            buyItemCol = self.clearReferenceJson(buyItemCol)
            content.append(buyItemCol)
            content[len(content)-1]['contents'][0]['text'] = '優惠折扣'
            content[len(content)-1]['contents'][1]['text'] = str(salePrice * -1)

        now = datetime.now()
        
        linkOrderId = now.strftime("%Y%m%d%H%M%S")

        for order in orders:
            if order.linkOrderId == "":
                order.linkOrderId = linkOrderId
            order.totalPrice = totalPrice
            order.save()

        buyItemCol = self.clearReferenceJson(buyItemCol)
        content.append(buyItemCol)
        content[len(content)-1]['contents'][0]['text'] = '總計'
        content[len(content)-1]['contents'][1]['text'] = str(totalPrice)

        message = FlexSendMessage(alt_text="購物車資訊", contents=DataConfirm)
        response = line_bot_api.push_message(self.to, message)
        return response , content

    def memberInfoFlex(self,displayName,phone,birthday):
        DataConfirm = self.getDataConfirm()
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
    if settings.TESTING == False:
        print (messageCallback)
    decodeToText = decodeJson(messageCallback)
    lineEvent = decodeToText.parse()    
    lineEvent = lineEvent.events[0]

    lineID = lineEvent.source.userId
    if settings.TESTING == False:
        profile = line_bot_api.get_profile(lineID)
        Display_name = profile.display_name
    elif settings.TESTING == True:
        Display_name = '洪嘉駿 Jason_Scend'
        
    MemberAction = memberAction(lineID = lineID,displayName = Display_name)
    member = MemberAction.getMember()
    LineMessage = lineMessage(lineID)

    try:
        classNahoo = fetchWebServiceData.nahoo()
    except:
        LineMessage.textMessage('目前系統維護中')
        return '目前系統維護中'
    switch = {
            '註冊-電話號碼': MemberAction.saveMemberPhone,
            '註冊-生日' : MemberAction.saveMemberBirth,
            
            #無用的跳出函式 MemberAction.normalMember
            '正常用戶' : MemberAction.normalMember,
            '正常用戶-已選擇商品類別': classNahoo.returnWebMenuData,
            '正常用戶-已選擇店點' : classNahoo.returnWebMenuData,
            '正常用戶-已選擇商品' : MemberAction.normalMember,
             }

    case = MemberAction.getSession()
    carouselTemplateMSG = CarouselTemplateGenerator.Generator()
    
    if lineEvent.type != 'postback':
        ClientMsg = lineEvent.message.text
    elif case != None and case.status == '正常用戶':
        ClientMsg = lineEvent.postback.data
    elif case != None and case.status == '正常用戶-已選擇商品類別':
        ClientMsg = lineEvent.postback.data
    elif case != None and case.status == '正常用戶-已選擇店點':
        ClientMsg = lineEvent.postback.data
    elif case != None and case.status == '正常用戶-已選擇商品':
        ClientMsg = lineEvent.postback.data
    elif case != None and case.status == '正常用戶-加料中':
        ClientMsg = lineEvent.postback.data
    else:
        ClientMsg = lineEvent.postback.params.date

    
    if ClientMsg == "點餐":
        MemberAction.createSession()
        MemberAction.updateSession('正常用戶')
        
    if ClientMsg == '結帳':
        order = shoppingCart.objects.filter(
            member__lineID=lineID, isPayed='False', cashOnDelivery=False).first()
        if order == None:
            LineMessage.textMessage('購物車內尚無商品')
            return JsonResponse({'response': 'OK' },safe=False)

        _linePay = linePay()
        _linePay.confirmUrl = 'https://www.nahoo.com.tw:8000'

        member.orderId +=  order.linkOrderId + ','
        _linePay.orderId =  order.linkOrderId

        member.save()
        productName = '結帳'    
        totalPrice = order.totalPrice
        amount = str(order.totalPrice)
        _linePay.reserveOrder(productName, amount,order.productImageUrl)
        LineMessage.textMessage("訂單成功，請點連結線上付款，或點選到店取貨付款按鈕。")
        LineMessage.textMessage(_linePay.paymentURL)
        MemberAction.updateSession('正常用戶')
        response = JsonResponse({'orderId': member.orderId})
        return response
    if ClientMsg == "使用到店取餐":
        orders = shoppingCart.objects.filter(
            member__lineID=lineID,cashOnDelivery = False ,isTaked=False, isPayed='False').order_by('updated_at')
        if orders == None:
            LineMessage = lineMessage(lineID)
            LineMessage.textMessage('目前沒有訂單可以使用到店取餐')
            return JsonResponse({'response': 'OK' },safe=False)

        for order in orders:
            #更新為到店取餐這個狀態
            order.cashOnDelivery = True
            order.save()
        orderId = orders[0].linkOrderId

        LineMessage = lineMessage(lineID)
        LineMessage.textMessage('您的訂單編號為 : ' + str(orderId))
        imgurURL = barCodeGenerator.runAndGetURL(str(orderId))
        LineMessage.imageMessage(imgurURL)

        return JsonResponse({'response': 'OK' },safe=False)

    if ClientMsg == '使用邀請碼':
        setting = systemSetting.objects.all().first()
        try:
            if setting.inviteCodeStatus == '1':
                LineMessage.textMessage('請輸入邀請碼(英文為小寫)')
                MemberAction.updateSession('正常用戶-等待輸入邀請碼')
            else:
                LineMessage.textMessage('系統尚未開啟邀請碼優惠')
                return JsonResponse({'response': 'OK' },safe=False)

        except:
            systemSetting.objects.create(inviteCodeStatus = '0', 
                                         autoReGeneratorInviteCode = 'True', 
                                         saleNumber = 10,
                                        )
            LineMessage.textMessage('系統尚未開啟邀請碼優惠')
        return JsonResponse({'response': 'OK' },safe=False)
        
    if ClientMsg == '檢視購物車':
        if member.address =='':
            LineMessage.textMessage('您尚未註冊會員，請輸入您的地址註冊會員')
            MemberAction.updateSession('註冊-地址')
        elif member.phone =='':
            LineMessage.textMessage('請輸入電話')
            MemberAction.updateSession('註冊-電話號碼')
            return JsonResponse({'response': 'OK' },safe=False)
        else:
            LineMessage.orderInfoFlex(lineID,member.displayName,member.phone,member.address)
            MemberAction.updateSession('正常用戶')
            return JsonResponse({'response': 'OK' },safe=False)
    if ClientMsg == "加料完畢":
        LineMessage.textMessage('請輸入訂購數量')
        MemberAction.updateSession('正常用戶-詢問訂購數量')
        return JsonResponse({'response': 'OK' },safe=False)

    if ClientMsg == "修改取餐人":
        LineMessage.textMessage("請輸入要修改的取餐人姓名")
        MemberAction.updateSession("正常用戶－修改取餐人")
        return JsonResponse({'response': 'OK' },safe=False)

    if ClientMsg == "修改電話":
        LineMessage.textMessage("請輸入要修改的電話資料")
        MemberAction.updateSession("正常用戶－修改電話")
        return JsonResponse({'response': 'OK' },safe=False)

    if ClientMsg == "修改訂單":
        orders = shoppingCart.objects.filter(
            member__lineID=lineID, isPayed='False',cashOnDelivery=False).order_by('updated_at')
        carouselItems = []

        if len(orders)==0:
            LineMessage.textMessage("購物車內尚無可修改之訂單")
            return JsonResponse({'response': 'OK' },safe=False)

        i = 0
        for item in orders:
            MessageActions = []
            name = item.itemName
            price = str(item.itemPrice)
            product = Product(item.productImage)

            MessageActions.append(carouselTemplateMSG.MessageAction(label='刪除' + str(i+1) + "." + name,
                                                                     text='刪除' + str(i+1) + "." + name))

            carouselItems.append(carouselTemplateMSG.carouselItem(thumbnail_image_url=product.pdtPicture,
                                                            title=name,
                                                            text='價格 :' + price,
                                                        action=MessageActions))

            carouselTemplateObjs = carouselTemplateMSG.carouselTemplate(alt_text = '修改訂單',
                                                         CarouselList = carouselItems)
            i += 1
        for carouse in carouselTemplateObjs:
            line_bot_api.push_message(LineMessage.to, carouse)
        return JsonResponse({'response': 'OK' },safe=False)

    if "刪除" in ClientMsg:
        requestDelName = ClientMsg.replace("刪除","")
        itemIndex , itemName = requestDelName.split(".")
        delTargetOrders = shoppingCart.objects.filter(member__lineID=lineID, isPayed='False',cashOnDelivery=False).order_by('updated_at')
        delTargetOrders[int(itemIndex)-1].delete()

        LineMessage.orderInfoFlex(lineID,member.displayName,member.phone,member.address)
        MemberAction.updateSession('正常用戶')
        return JsonResponse({'response': 'OK' },safe=False)
    if ClientMsg == "修改地址":
        LineMessage.textMessage("請輸入要修改的地址資料")
        MemberAction.updateSession("正常用戶－修改地址")
        return JsonResponse({'response': 'OK' },safe=False)


    case = MemberAction.getSession()

    MessageActions = []
    carouselItems = []
    carouselItems = []
    if case != None:
        try:
            if len(ClientMsg.split(","))>0:
                storeId = ClientMsg.split(",")[0]
                reciveData = switch[case.status](storeId)
            else:
                reciveData = switch[case.status](ClientMsg)
        except:
            pass
        if case.status == '正常用戶':
            config = configparser.ConfigParser()
            config.read('config.ini')
            # config.read("/Users/Jason/Scripts/LinePay_20200305/LinePay/pos-bot/config.ini")

            hq = config['Shop']['hqID']

            shopList = []
            for shop in classNahoo.queryShopIds(hq):
                shopList.append(shop)
                        
            for shop in shopList:
                MessageActions = []
                _shopInfo = classNahoo.shopInfo(shop)
                if _shopInfo == None:
                    continue
                shpAddress = _shopInfo["shpAddress"]
                shpShopName = _shopInfo["shpShopName"]
                imageUrl = _shopInfo["shpLogoPicturePath"]
                MessageActions.append(carouselTemplateMSG.PostbackAction(label = '選擇該店訂餐',
                                                                text = None,
                                                                data = str(shop),
                                                                    ))
                MessageActions.append(carouselTemplateMSG.MessageAction(label='回到主選單',
                                                                        text='點餐',))
                                                                        
                MessageActions.append(carouselTemplateMSG.MessageAction(label='檢視購物車',
                                                                        text='檢視購物車',))
                carouselItems.append(carouselTemplateMSG.carouselItem(thumbnail_image_url = imageUrl,
                                                                title = shpShopName,
                                                                text = shpAddress,
                                                                action = MessageActions))
            carouselTemplateObjs = carouselTemplateMSG.carouselTemplate(alt_text = '店鋪列表',
                                                        CarouselList = carouselItems)
            for carouse in carouselTemplateObjs:
                line_bot_api.push_message(LineMessage.to, carouse)
            MemberAction.updateSession('正常用戶-已選擇店點')
            return JsonResponse({'response': 'OK' },safe=False)
        if case.status == '正常用戶-已選擇店點':
            #刪除因為中途跳開點餐程序的未完成訂單（購買數量為0）的產品
            shoppingCart.objects.filter(member__lineID = lineID , isPayed = 'False' , productAmount = 0).delete()
            
            orders = shoppingCart.objects.filter(member__lineID=lineID, isPayed = 'False',cashOnDelivery = False)
            
            if len(orders) != 0:
                if orders[0] != None and orders[0].shopId != ClientMsg and orders[0].productAmount > 0:
                    LineMessage.textMessage("抱歉，不能跨店點餐，請先將購物車內的商品結帳")
                    LineMessage.orderInfoFlex(lineID,member.displayName,member.phone,member.address)
                    return JsonResponse({'response': '抱歉，不能跨店點餐，請先將購物車內的商品結帳' },safe=False)
            carouselTemplateObjs = None
            menu = reciveData
            if menu == '該店沒有菜單':
                LineMessage.textMessage(menu)
                return JsonResponse({'response': 'OK' },safe=False)
            for product in menu["items"]:
                MessageActions = []
                itmItemName = product['itmItemName']
                itemClassId = str(product['id'])
                product = Product(product["itmPicturePath"])
                
                shopID = ClientMsg
                MessageActions.append(carouselTemplateMSG.PostbackAction(label = itmItemName[0:20],
                                                                        text = None,
                                                                        data = shopID +","+itmItemName[0:20]+"," + itemClassId,
                                                                        ))
                                                                
                carouselItems.append(carouselTemplateMSG.carouselItem(thumbnail_image_url = product.pdtPicture,
                                                                title = itmItemName[0:20],
                                                                text = itmItemName,
                                                            action = MessageActions))
               
            carouselTemplateObjs = carouselTemplateMSG.carouselTemplate(alt_text = '菜單',
                                                         CarouselList = carouselItems)
            
            for carouse in carouselTemplateObjs:
                line_bot_api.push_message(LineMessage.to, carouse)
            MemberAction.updateSession('正常用戶-已選擇商品類別')
            return JsonResponse({'response': 'OK' },safe=False)

        if case.status == '正常用戶-已選擇商品類別': 
            if len(ClientMsg.split(',')) == 1:
                return JsonResponse({'response': 'OK' },safe=False)

            order = shoppingCart.objects.filter(member__lineID=lineID, isPayed = 'False',cashOnDelivery = False).first()
            
            shopID , productClassName , productClassId = ClientMsg.split(',')

            if order != None and order.shopId != shopID:
                LineMessage.textMessage("抱歉，不能跨店點餐，請先將購物車內的商品結帳")
                LineMessage.orderInfoFlex(lineID,member.displayName,member.phone,member.address)
                return JsonResponse({'response': '抱歉，不能跨店點餐，請先將購物車內的商品結帳' },safe=False)
                
            carouselTemplateObjs = None
            menu = reciveData
            if menu == '該店沒有菜單':
                LineMessage.textMessage(menu)
                return JsonResponse({'response': 'OK' },safe=False)
            for product in menu["products"]:
                MessageActions = []
                
                #依照用戶提出的飲品類別ID 推送該類別的品項
                if product["itemId"] == int(productClassId):
                    pdtProductName = product['pdtProductName']
                    pdtPrice = str(product['pdtPrice'])
                    product = Product(product["pdtPicturePath"])
                    
                    MessageActions.append(carouselTemplateMSG.PostbackAction(label = pdtProductName[0:20],
                                                                            text = None,
                                                                            data = shopID +","+pdtProductName[0:20]+"," + pdtPrice + "," +product.pdtPicture + ","+ productClassName + "," + productClassId,
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
            return JsonResponse({'response': 'OK' },safe=False)
        
        if case.status == '正常用戶-已選擇商品':
            if len(ClientMsg.split(','))== 3:
                shopID , productClassName , productClassId = ClientMsg.split(',')
                menu = switch['正常用戶-已選擇店點'](shopID)
                if menu == '該店沒有菜單':
                    LineMessage.textMessage(menu)
                    return JsonResponse({'response': 'OK' },safe=False)
                for product in menu["products"]:
                    MessageActions = []
                    
                    #依照用戶提出的飲品類別ID 推送該類別的品項
                    if product["itemId"] == int(productClassId):
                        pdtProductName = product['pdtProductName']
                        pdtPrice = str(product['pdtPrice'])
                        product = Product(product["pdtPicturePath"])
                        
                        MessageActions.append(carouselTemplateMSG.PostbackAction(label = pdtProductName[0:20],
                                                                                text = None,
                                                                                data = shopID +","+pdtProductName[0:20]+"," + pdtPrice + "," +product.pdtPicture + ","+ productClassName + "," + productClassId,
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
                return JsonResponse({'response': 'OK' },safe=False)
                
            LineMessage.textMessage('請選擇甜度、溫度限各"1"種。大杯可加價購"3"種加料，中杯可加價購"2"種加料。如不加料請按加料完畢。')
            shopID , pdtProductName , pdtPrice , productImage , itemClassName , productClassId = ClientMsg.split(',')
            
            addCart(lineID,shopID,pdtProductName,pdtPrice,productImage, itemClassName , productClassId)           
            
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
            try:
                int(pdtProductName)
                LineMessage.textMessage('請選擇正確的加料產品')
            except:
                LineMessage.textMessage(pdtProductName + '加' + name + '。如果不再加料請按加料完畢')
                order = shoppingCart.objects.filter(member__lineID = lineID ,  
                                            itemName = pdtProductName , isPayed = 'False').order_by('-updated_at').first()
                order.addOnNameHistory += ','+ name
                order.addOnPriceHistory += ','+ price
                order.save()

        if case.status == "正常用戶－修改取餐人":
            member.displayName = ClientMsg
            member.save()
            LineMessage.textMessage('已更新資料為' + ClientMsg)
            LineMessage.orderInfoFlex(lineID,member.displayName,member.phone,member.address)
            MemberAction.updateSession('None')
            return JsonResponse({'response': 'OK' },safe=False)

        if case.status == "正常用戶－修改電話":
            member.phone = ClientMsg
            member.save()
            LineMessage.textMessage('已更新資料為' + ClientMsg)
            LineMessage.orderInfoFlex(lineID,member.displayName,member.phone,member.address)
            MemberAction.updateSession('None')
            return JsonResponse({'response': 'OK' },safe=False)

        if case.status == "正常用戶－修改地址":
            member.address = ClientMsg
            member.save()
            LineMessage.textMessage('已更新資料為' + ClientMsg)
            LineMessage.orderInfoFlex(lineID,member.displayName,member.phone,member.address)
            MemberAction.updateSession('None')
            return JsonResponse({'response': 'OK' },safe=False)

        if case.status == '正常用戶-檢查繼續訂餐':
            if ClientMsg == '是':
                order = shoppingCart.objects.filter(member__lineID = lineID , isPayed = 'False').order_by('-updated_at').first()
                #輸出店家列表
                case.status = '正常用戶 shopId:' + order.shopId
            if ClientMsg == '否':
                if member.address =='':
                    LineMessage.textMessage('請輸入送餐地址')
                    MemberAction.updateSession('註冊-地址')
                    return JsonResponse({'response': 'OK' },safe=False)
                else:
                    setting = systemSetting.objects.all().first()
                    try:
                        if setting.inviteCodeStatus == '1':
                            carouselTemplateObj = TemplateSendMessage(
                                alt_text='請問是否使用邀請碼優惠?',
                                template=ConfirmTemplate(
                                    text='請問是否使用邀請碼優惠?',
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
                            MemberAction.updateSession('正常用戶-檢查是否使用邀請碼')
                        else:
                            LineMessage.orderInfoFlex(lineID, member.displayName, member.phone, member.address)
                    except:
                        systemSetting.objects.create(   inviteCodeStatus = '0', 
                                                        autoReGeneratorInviteCode = 'True', 
                                                        saleNumber = 10,
                        )
                        LineMessage.orderInfoFlex(lineID, member.displayName, member.phone, member.address)
                    return JsonResponse({'response': 'OK' },safe=False)

        if case.status == '正常用戶-詢問訂購數量':
            match = re.search(r'[1-9]',str(ClientMsg))
            if match == None or match.endpos<0:
                LineMessage.textMessage('請輸入正確的數字')
                response = JsonResponse({'response': 'productAmount Must be number'})
                return response
            
            elif match.endpos>0 and int(ClientMsg) <= 0:
                LineMessage.textMessage('請輸入大於0的數字')
                response = JsonResponse({'response': 'productAmount Must be number'})
                return response

            elif match.endpos>0:
                #因為會發生訂完東西後，再點回點餐，又剛好沒選錯店，那這個時候前後比訂單就會代碼不同了
                #為了解決這個問題，就將所有後來加入，但又同一間店的訂單歸到第一筆訂單的代碼中
                lastLinkOrderId = ""
                orders = shoppingCart.objects.filter(member__lineID = lineID , isPayed = 'False').order_by('-updated_at')

                #獲取最早的一筆訂單代碼，且不能是已經設定為到店取餐的訂單
                lastLinkOrderId = shoppingCart.objects.filter(member__lineID = lineID , isPayed = 'False',cashOnDelivery = False).first().linkOrderId
           
                #最接近目前時間的一筆訂單
                newestOrder = orders[0]
                newestOrder.productAmount = int(ClientMsg)
                newestOrder.linkOrderId = lastLinkOrderId
                newestOrder.save()
                case.status = '正常用戶-詢問是否繼續訂餐'
                    
        if case.status == '正常用戶-檢查是否使用邀請碼':
            if ClientMsg == '是':
                LineMessage.textMessage('請輸入邀請碼(英文為小寫)，訂單可享折扣優惠')
                MemberAction.updateSession('正常用戶-等待輸入邀請碼')
                return JsonResponse({'response': 'OK' },safe=False)
            if ClientMsg == '否':
                LineMessage.orderInfoFlex(lineID, member.displayName, member.phone, member.address)

        if case.status == '正常用戶-等待輸入邀請碼':
            isUseInviteCode = False
            memberInfo = MemberAction.checkInviteCode(ClientMsg)
            usingThisInviteCodeUser = lineID
            thisInviteCodeOwner_LineID = ''
            thisOwnerRecommendHistory = ''
            if len(memberInfo) > 0:
                #剛剛用戶輸入的邀請碼擁有者是誰
                thisInviteCodeOwner_LineID = memberInfo[0].owner.lineID

                #該擁有者已經推薦過誰了
                thisOwnerRecommendHistory = memberInfo[0].owner.recommendHistory
            
                if thisInviteCodeOwner_LineID == usingThisInviteCodeUser:
                    LineMessage.textMessage('抱歉，自己不能用自己的邀請碼打折')
                    carouselTemplateObj = TemplateSendMessage(
                    alt_text='請問是否繼續使用邀請碼優惠?',
                    template=ConfirmTemplate(
                        text='請問是否繼續使用邀請碼優惠?',
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
                    MemberAction.updateSession('正常用戶-檢查是否使用邀請碼')
                    return JsonResponse({'response': 'OK' },safe=False)
                    
                if usingThisInviteCodeUser in thisOwnerRecommendHistory:
                    LineMessage.textMessage('抱歉，您已使用過對方的邀請碼')
                    carouselTemplateObj = TemplateSendMessage(
                    alt_text='請問是否繼續使用邀請碼優惠?',
                    template=ConfirmTemplate(
                        text='請問是否繼續使用邀請碼優惠?',
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
                    MemberAction.updateSession('正常用戶-檢查是否使用邀請碼')
                    return JsonResponse({'response': 'OK' },safe=False)
                else:
                    memberInfo[0].status = "使用中"
                    inviteCodeUser = inviteCodeManager.objects.filter(owner__lineID = MemberAction.lineID).first().owner
                    memberInfo[0].user = inviteCodeUser
                    memberInfo[0].save()
                    # memberInfo[0].recommendHistory += usingThisInviteCodeUser + ','
                    # memberInfo[0].save()
                isUseInviteCode = True
                LineMessage.textMessage('邀請碼正確，訂單金額已折扣')

                LineMessage.orderInfoFlex(lineID, member.displayName, member.phone, member.address, isUseInviteCode,inviteCodeNumber = memberInfo[0].code)
                MemberAction.updateSession('正常用戶')
                return JsonResponse({'response': 'OK' },safe=False)
            else:
                LineMessage.textMessage('邀請碼已使用過或是輸入錯誤')
                carouselTemplateObj = TemplateSendMessage(
                    alt_text='請問是否繼續使用邀請碼優惠?',
                    template=ConfirmTemplate(
                        text='請問是否繼續使用邀請碼優惠?',
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
                MemberAction.updateSession('正常用戶-檢查是否使用邀請碼')
                return JsonResponse({'response': 'OK' },safe=False)

        if case.status == '註冊-電話號碼':
            if member.birthDay == '':
                LineMessage.datetimePicker()
                MemberAction.updateSession('註冊-生日')
                return JsonResponse({'response': 'OK' },safe=False)
            else:
                return JsonResponse({'response': 'OK' },safe=False)
        if case.status == '註冊-地址':
            member.address = ClientMsg
            member.save()
            if member.phone == '':
                LineMessage.textMessage('請輸入送餐電話')
                MemberAction.updateSession('註冊-電話號碼')
                return JsonResponse({'response': 'OK' },safe=False)
            else:
                LineMessage.orderInfoFlex(
                    lineID, member.displayName, member.phone, member.address)
                MemberAction.updateSession('正常用戶')
                return JsonResponse({'response': 'OK' },safe=False)
        if case.status == '註冊-生日':
            LineMessage.textMessage('您好'+member.displayName+',您已註冊成功，請至購物車結帳')
            MemberAction.updateSession('正常用戶')
            return JsonResponse({'response': 'OK' },safe=False)
        
        if '正常用戶 shopId:' in case.status:  # '正常用戶 shopId:' + order.shopId    繼續點餐
            shopId = case.status.split('shopId:')[1]
            menu = classNahoo.returnWebMenuData(shopId)
            
            if menu == '該店沒有菜單':
                LineMessage.textMessage(menu)
                return JsonResponse({'response': 'OK' },safe=False)
            for product in menu["items"]:
                MessageActions = []
                itmItemName = product['itmItemName']
                itemClassId = str(product['id'])
                product = Product(product["itmPicturePath"])
                
                MessageActions.append(carouselTemplateMSG.PostbackAction(label = itmItemName[0:20],
                                                                        text = None,
                                                                        data = shopId +","+itmItemName[0:20]+"," + itemClassId,
                                                                        ))
                                                                
                carouselItems.append(carouselTemplateMSG.carouselItem(thumbnail_image_url = product.pdtPicture,
                                                                title = itmItemName[0:20],
                                                                text = itmItemName,
                                                            action = MessageActions))
               
            carouselTemplateObjs = carouselTemplateMSG.carouselTemplate(alt_text = '菜單',
                                                         CarouselList = carouselItems)
            
            for carouse in carouselTemplateObjs:
                line_bot_api.push_message(LineMessage.to, carouse)
            MemberAction.updateSession('正常用戶-已選擇商品類別')
            return JsonResponse({'response': 'OK' },safe=False)

        
        
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
                                    alt_text='是否繼續點選其它產品?',
                                    template=ConfirmTemplate(
                                        text='是否繼續點選其它產品?',
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

        
    return JsonResponse({'response': 'OK' },safe=False)


#付款狀態確認
def confirm(request):
    orderId = request.GET["orderId"]

    #去訂單資料庫查看這筆訂單付款的會員是誰
    memberInfo = shoppingCart.objects.filter(
        linkOrderId=orderId).first().member
    LineMessage = lineMessage(memberInfo.lineID)
    LineMessage.textMessage('付款成功，您的訂單編號為 : ' + str(orderId))

    

    shoppingOrders = shoppingCart.objects.filter(member__lineID=memberInfo.lineID, isPayed = 'False')
    
    #如果用戶重複刷新頁面就會出現這個訊息
    if len(shoppingOrders) == 0 or shoppingOrders == None:
        response = JsonResponse({'response': 'Payment is successful, please close this page'}, safe=False, json_dumps_params={
                                'ensure_ascii': False})
        return response

    for order in shoppingOrders:
        order.isPayed = 'True'
        order.save()

    imgurURL = barCodeGenerator.runAndGetURL(str(orderId))
    LineMessage.imageMessage(imgurURL)

    MemberAction = memberAction(
        lineID=memberInfo.lineID, displayName=memberInfo.displayName)
    setting = systemSetting.objects.all().first()

    if shoppingOrders[0].inviteCode != '':
        #刪除該邀請碼，因為都已經結帳完成了
        inviteCodeInfo = inviteCodeManager.objects.filter(code= shoppingOrders[0].inviteCode).first()
        inviteOwner = inviteCodeInfo.owner
        inviteOwner.recommendHistory += inviteCodeInfo.user.lineID + ','
        inviteOwner.save()
        inviteCodeInfo.delete()

    #開啟邀請碼系統
    if setting.inviteCodeStatus == '1':
        MemberAction.reGeneratorInviteCode(memberInfo)
        #因為每次結帳都會改變邀請碼，所以要把還沒用過的邀請碼要儲存起來，讓人兌換
        getPos = random.randint(5, 32)
        newInviteCodeNumber = uuid.uuid1().hex[getPos-4:getPos]
        MemberAction.saveUsedInviteCode(owner = memberInfo,code = newInviteCodeNumber)
        LineMessage.textMessage('恭喜您獲得一組('+str(setting.saleNumber)+'折)邀請碼：' + str(newInviteCodeNumber) + '您可以轉傳給一位朋友使用。')
        response = JsonResponse({'response': 'Payment is successful, please close this page'}, safe=False, json_dumps_params={
                                'ensure_ascii': False})
        return response
    else:
        response = JsonResponse({'response': 'Payment is successful, please close this page'}, safe=False, json_dumps_params={
                                'ensure_ascii': False})
        return response
    

def settingInviteCode(request):
    inviteCodeStatus = request.GET["inviteCodeStatus"]
    systemSetting.objects.all().delete()
    setting = systemSetting(inviteCodeStatus = inviteCodeStatus)
    setting.save()
    response = JsonResponse({'inviteCodeStatus': inviteCodeStatus})
    return response

def queryOrderByCode(request):
    orderId = request.GET["orderId"]
    orders = shoppingCart.objects.filter(member__orderId__contains = orderId , isPayed = 'True', isTaked = False).values().order_by('updated_at')
    response = JsonResponse({'data': list(orders) },safe=False)
    return response

def queryAllOrder(request):
    orders = shoppingCart.objects.filter(isTaked = False).values().order_by('updated_at')
    response = JsonResponse({'data': list(orders) },safe=False)
    
    #解析DB輸出的所有訂單
    responseToJson = json.loads(response.content)

    #開始進行訂單分群作業
    orderIdLi = []
    for order in responseToJson['data']:
        #先知道所有訂單的編碼
        orderIdLi.append(order["linkOrderId"])

    #去除重複
    orderIds = list(set(orderIdLi))
    
    classificationOrder = []
    #經過萃取過的訂單編碼具有唯一性
    for Id in orderIds:
        subClassOrder = []
        #個別訂單編碼去查找DB
        classOrder = shoppingCart.objects.filter(linkOrderId = Id , isPayed = 'True' , isTaked = False).order_by('updated_at')
        classOrder = classOrder.values()
        
        for subOrder in classOrder:
            subClassOrder.append(subOrder)
        classificationOrder.append(subClassOrder)
    response = JsonResponse({'data': list(classificationOrder) },safe=False)
    responseToJson = json.loads(response.content)
    
    #修改Json檔案格式，兩個子訂單顯示在一起外，總價顯示一個地方就好
    totalPriceList = []
    for classItem in responseToJson['data']:
        itemPrice = 0
        for item in classItem:
            subPrice = 0
            itemPrice = str(item['totalPrice'])
            linkOrderId = item['linkOrderId']
            subPrice += item['itemPrice']
            for addonPrice in item['addOnPriceHistory'].split(","):
                if addonPrice != '':
                    #總價 + 加料金額
                    subPrice += int(addonPrice)

            #總價 * 購買數量
            subTotal = subPrice * int(item['productAmount'])
            del item['totalPrice']
            del item['linkOrderId']
            item['subPrice'] = subPrice
            item['subTotal'] = subTotal

        Member = member.objects.filter(id=item['member_id']).first()
        classItem.append('totalPrice = ' + str(itemPrice))
        classItem.append('OrderId = ' + linkOrderId)
        classItem.append('Member displayName = ' + Member.displayName)
        classItem.append('Member address = ' + Member.address)
        classItem.append('Member phone = ' + Member.phone)
        



    response = JsonResponse(json.loads(json.dumps(responseToJson)),safe=False)
    return response

def setIsTakeOrderByCode(request):
    orderId = request.GET["orderId"]
    orders = shoppingCart.objects.filter(
        linkOrderId=orderId).order_by('updated_at')
    orders = orders.values()

    orders.update(isTaked=True)

    response = JsonResponse({'response': 'OK' },safe=False)
    return response
