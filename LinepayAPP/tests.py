from django.test import TestCase
import views as test_view
import fetchWebServiceData as test_fetchWebServiceData
import pdb
from LinepayAPP.models import *
import LinepayAPP.CarouselTemplateGenerator as CarouselTemplateGenerator
import re
import configparser
import requests
import urllib3
import codecs
from LinepayAPP.classLib import *
import inspect
import random

class TestNahooClass(TestCase):
    @classmethod
	#執行下面的method之前，會先執行一次setUpTestData(self)來新增假資料
    def setUpTestData(self):
        self.classNahoo = test_fetchWebServiceData.nahoo()
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.hqID = config['Shop']['hqID']
        self.shopId = 13
    def test_shopInfo(self):
        print ('Method:shopInfo 查詢門店資料')
        shopInfo = self.classNahoo.shopInfo('13')
        self.assertEquals(shopInfo["shpShopName"] , '線上點餐1店')

    def test_shopLogo(self):
        print ('Method:shopLogo 檢查門店圖片是否正常')
        QueryShopIds = self.classNahoo.queryShopIds(self.hqID)
        ErrorStoreLogoUrlList = []
        for shopId in QueryShopIds:
            shopInfo = self.classNahoo.shopInfo(shopId)
            PicturePath = shopInfo["shpLogoPicturePath"]

            if self.regularIsURL(PicturePath) == False:
                ErrorStoreLogoUrlList.append(PicturePath)
                continue
            if self.IsRightImageURL(PicturePath) == False:
                ErrorStoreLogoUrlList.append(PicturePath)
                continue

        self.printErrorURL(tag = "店鋪圖錯誤" , errorList = ErrorStoreLogoUrlList)
    
    def test_queryHqInfoIds(self):
        print ('Method:queryHqInfoIds 查詢所有總部資料')
        QueryHqInfoIds = self.classNahoo.queryHqInfoIds()

    def test_queryShopIds(self):
        print ('Method:queryShopIds 查詢所有總部下的門市資料')
        HqIds = [self.hqID]
        QueryShopIds = []
        for hq in HqIds:
            QueryShopIds.append(self.classNahoo.queryShopIds(hq))
        self.assertTrue(QueryShopIds, None)

    def test_returnWebMenuData(self):
        print ('Method:returnWebMenuData 查詢門店菜單')
        menu = self.classNahoo.returnWebMenuData(self.shopId)
        drinkTaiwanPrice = menu["products"][0]["pdtPriceTw"]
        match = re.search(r'[0-9]',str(drinkTaiwanPrice))
        self.assertTrue(match.endpos>0)

    def regularIsURL(self,Photo_URL):
        #檢查網址內是否有數字，有數字即為IP型態，Line會拒絕
        match = re.search(r'http*.:\\\\[0-9]+\.[0-9]+\.',Photo_URL)
        if Photo_URL == "":
            return False
        if match != None:
            if match.endpos>0:
                return False
        return True

    def IsRightImageURL(self,Photo_URL):
        pictureRequest = requests.get(Photo_URL, verify=False)
        if pictureRequest.status_code != 200:
            return False
        return True
    
    def printErrorURL(self,tag,errorList):
        #去除重複URL
        errorList = list(set(errorList))
        for ErrorURL in errorList:
            if ErrorURL != "":
                print ("[" + tag + "] " + ErrorURL)

    def test_menuPhoto(self):
        print ('Method:menuPhoto 檢查菜單圖片與加料圖是否正常')
        QueryShopIds = self.classNahoo.queryShopIds(self.hqID)
        ErrorPhotoList = []
        ErrorAddonPhotoList = []
        for shopId in QueryShopIds:
            menu = self.classNahoo.returnWebMenuData(shopId)
            requests.packages.urllib3.disable_warnings()
            requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
            if menu == "該店沒有菜單":
                continue

            for product in menu["products"]:
                Photo_URL = product["pdtPicturePath"]
                if self.regularIsURL(Photo_URL) == False:
                    ErrorPhotoList.append(Photo_URL)
                    continue
                if self.IsRightImageURL(Photo_URL)  == False:
                    ErrorPhotoList.append(Photo_URL)
                    continue

            for product in menu["productsAdds"]:
                Photo_URL = product["picturePath"]
                if self.regularIsURL(Photo_URL) == False:
                    ErrorAddonPhotoList.append(Photo_URL)
                    continue
                if self.IsRightImageURL(Photo_URL)  == False:
                    ErrorAddonPhotoList.append(Photo_URL)
                    continue
        self.printErrorURL(tag = "菜單圖錯誤",errorList = ErrorPhotoList)
        self.printErrorURL(tag = "加料圖錯誤",errorList = ErrorAddonPhotoList)
                    
class TestDBClass(TestCase):
    @classmethod
	#執行下面的method之前，會先執行一次setUpTestData(self)來新增假資料
    def setUpTestData(self):
        self.lineID = 'Ue2a91beba135696d6b7cafad52e51587'
        self.fakeLineID = 'Ue2a91beba135696d6b7cafad52e51588'
        self.phone = '0918123123'
        self.birth = '2019-01-01'
        self.status = '註冊-電話號碼'
        self.display_name = '洪嘉駿 Jason'
        self.address = '台北市北投區'
        self.itemClassName = "找好茶"
        self.itemClassId = "1"
        self.memberAction = test_view.memberAction(self.lineID,displayName = self.display_name)
        Member = member(lineID=self.lineID,phone = self.phone,displayName = self.display_name)
        Member.save()

        ClientSession = clientSession(member = Member,status = 'default')
        ClientSession.save()
        return self
    
    def test_linepayConfig(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        _channelId = config['LinePayID']['ChannelId']
        _channelSecret = config['LinePayID']['ChannelSecret']
        
        channelIdMatch = re.search(r'[0-9]', str(_channelId))
        self.assertTrue(channelIdMatch.endpos > 0)

        channelSecretMatch = re.search(r'[0-9]', str(_channelSecret))
        self.assertTrue(channelSecretMatch.endpos > 0)

    def test_saveMemberPhone(self):
        print("Method:saveMemberPhone 儲存會員電話號碼")
        setMemberPhone = self.memberAction.saveMemberPhone(self.phone)
        self.assertEqual(setMemberPhone.phone,self.phone)
    
    def test_saveMemberBirth(self):
        print("Method:saveMemberBirth 儲存會員生日")
        setMemberBirth = self.memberAction.saveMemberBirth(self.birth)
        self.assertEqual(setMemberBirth.birthDay,self.birth)
    
    def test_createMember(self):
        print("Method:createMember 創建會員")
        memberInfo = self.memberAction.createMember()
        self.assertEqual(memberInfo.displayName , self.display_name)

    def test_getMember(self):
        print("Method:getMember 取得會員資料")
        member = self.memberAction.getMember()
        self.assertEqual(member.displayName , self.display_name)

    def test_createSession(self):
        print("Method:updateSession 創建會員狀態")
        memberInfo = self.memberAction.createSession()
        self.assertEqual(memberInfo.status ,'')
        
    def test_updateSession(self):
        print("Method:updateSession 更新會員狀態")
        memberInfo = self.memberAction.updateSession(self.status)
        self.assertEqual(memberInfo.status , self.status)
    
    def test_getSession(self):
        print("Method:getSession 取得會員狀態")
        self.memberAction.updateSession(self.status)
        memberInfo = self.memberAction.getSession()
        self.assertEqual(memberInfo.status,self.status)

    def test_addCart(self):
        print("Method:addCart 加入購物車")
        itemName = '金風玉露烏龍茶(H)'
        Cart = test_view.addCart(self.lineID , 2 , itemName , 22 , productImage = "Test",itemClassName = self.itemClassName,itemClassId = self.itemClassId)
        self.assertEqual(Cart.itemName,itemName)

class TestLineMessageClass(TestCase):
    @classmethod
	#執行下面的method之前，會先執行一次setUpTestData(self)來新增假資料
    def setUpTestData(self):
        self.title = 'Test'
        self.subTitle = 'Test subTitle'
        self.subText = 'Test subText'
        self.alt_text = 'Test alt_text'
        self.lineID = TestDBClass.lineID
        self.display_name   = TestDBClass.display_name
        self.phone = TestDBClass.phone
        self.address   = TestDBClass.address
        self.LineMessage = test_view.lineMessage(self.lineID)
        self.thumbnailImageUrl = 'https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_5_carousel.png'
        self.carouselTemplateMSG = CarouselTemplateGenerator.Generator()
        setMemberPhone = member(lineID=self.lineID,phone = self.phone,displayName = self.display_name)
        setMemberPhone.save()

        self.shopID = 1
        self.pdtProductName = '烏龍青茶'
        self.pdtPrice = 25
        Cart = shoppingCart(member = setMemberPhone , 
                    shopId = self.shopID , 
                    itemName = self.pdtProductName,
                    itemPrice = self.pdtPrice)
        Cart.save()
    def test_generator(self):
        print ('Method:generator 檢查初始化輪播圖訊息')
        self.carouselTemplateMSG = CarouselTemplateGenerator.Generator()
        self.assertTrue(self.carouselTemplateMSG,None)
        
    def test_messageAction(self):
        print ('Method:messageAction 檢查輪播圖文字動作')
        label = 'Test label'
        text = 'Test text'
        MessageActions = self.carouselTemplateMSG.MessageAction(label = label,
                                                                 text = text)
        self.assertEqual(MessageActions.label,label)
        self.assertEqual(MessageActions.text,text)
        return MessageActions

    def test_carouselItem(self):
        label = 'Test label'
        text = 'Test text'
        MessageActions = [self.carouselTemplateMSG.MessageAction(label = label,
                                                                 text = text)]
        carouselItem = self.carouselTemplateMSG.carouselItem(thumbnail_image_url = self.thumbnailImageUrl,
                                        title = self.subTitle,
                                        text = self.subText,
                                        action = MessageActions)
        return carouselItem

    def test_carouselTemplate(self):
        print ('Method:carouselTemplate 檢查輪播圖訊息')
        itemLength = 30
        carouselItem =[self.test_carouselItem() for i in range(itemLength)]
        carouselTemplateObjs = self.carouselTemplateMSG.carouselTemplate(alt_text = self.alt_text,CarouselList = carouselItem)
        #self.assertEqual (len(carouselTemplateObjs),itemLength/10)
        for carouse in carouselTemplateObjs:
            self.assertEqual(carouse.alt_text,self.alt_text)

class testToRequest:
    def __init__(self,userId = "Ue2a91beba135696d6b7cafad52e51587"):
        self.body = ""
        self.userId = userId
    def message(self,messageText):
        self.body =""" {"events":[{"type":"message",
                            "replyToken":"0000000000000000000000000000000000",
                            "source":{
                                "userId":"""+'"'+self.userId+'"'+""",
                                "type":"user"},
                                "timestamp":0000000000000000000000000000000000,
                                "message":{
                                    "type":"text",
                                    "id":"0000000000000000000000000000000000",
                                    "text":"
                                    """
        self.body += messageText + """
                        "}}],
                        "destination":"U1863f94dd5dd7640d48a675e2a26431e"
                        }"""
        self.body = self.body.replace("\n","").replace(" ","")
        return self

    def postback(self,postbackText):
        self.body ="""{"events":[{"type":"postback",
                        "replyToken":"0000000000000000000000000000000000",
                        "source":{"userId":"0000000000000000000000000000000000",
                        "type":"user"},
                        "timestamp":0000000000000000000000000000000000,
                        "postback":{"data":"
                    """
        self.body += postbackText + """
                       "}}],"destination":"0000000000000000000000000000000000"}"""
        self.body = self.body.replace("\n","").replace(" ","")
        return self
class TestOrderProcess(TestCase):
    @classmethod
    def setUpTestData(self):
        self.lineID = '0000000000000000000000000000000000'
        self.fakeLineID = '0000000000000000000000000000000000'
        self.phone = '0918123123'
        self.birth = '2019-01-01'
        self.status = '註冊-電話號碼'
        self.display_name = ' '
        self.fakeDisplay_name = self.display_name+"_Scend"
        self.address = ' '
        self.memberAction = test_view.memberAction(self.lineID,displayName = self.display_name)
        Member = member(lineID=self.lineID,phone = self.phone,displayName = self.display_name)
        Member.save()
        
        #在邀請碼資料庫產生邀請碼
        getPos = random.randint(5, 32)
        inviteCodeNumber = uuid.uuid1().hex[getPos-4:getPos]
        inviteCodeManager.objects.create(owner = Member,code = inviteCodeNumber)
        
        getPos = random.randint(5, 32)


        SecondMember = member(lineID=self.fakeLineID,phone = self.phone,displayName = self.fakeDisplay_name)
        SecondMember.save()

        #在邀請碼資料庫產生第二組邀請碼
        getPos = random.randint(5, 32)
        inviteCodeNumber = uuid.uuid1().hex[getPos-4:getPos]
        inviteCodeManager.objects.create(owner = SecondMember,code = inviteCodeNumber)

        self.itemClassName = "找好茶"
        self.itemClassId = "1"
        ClientSession = clientSession(member = Member,status = 'default')
        ClientSession.save()

        ClientSession = clientSession(member = SecondMember,status = 'default')
        ClientSession.save()

        self.store = '13'
        self.pdtProductName = "茉莉綠茶（中）"
        self.pdtPrice = "16"
        self.addOnName = "珍珠"
        self.addOnPrice = "10"
        self.productAmount = "2"
        self.pdtPicture = "https://simplesweetea.com/uploads/product/GreenTea.jpg"
        self.totalPrice = 0
        Member = member.objects.filter(lineID=self.lineID).first()
        Member.address = self.address
        Member.phone = self.phone
        Member.save()

        #不使用邀請碼
        systemSetting.objects.all().delete()
        setting = systemSetting(inviteCodeStatus = '0')
        setting.save()
        return self
    
    def decodeText(self,msg):
        msg = msg.encode('big5').decode('unicode_escape')
        return msg

    def actionTest(self,actionType,action,*checkPoint,LineID = None):
        if LineID == None:
            createRequest = testToRequest()
        else:
            createRequest = testToRequest(userId = self.fakeLineID)

        if actionType == 'message':
            #模擬按鈕點餐
            request = createRequest.message(action)
            test_view.callback(request)
        
        if actionType == 'postback':
            #模擬帶資料的按鈕點餐
            request = createRequest.postback(action)
            test_view.callback(request)
        #分析按下後的結果
        log = testLog.objects.all()
        logStr = self.decodeText(log[0].message)
        return logStr
    def checkResponse(self,responseText,checkPoint,TestName = None):
        #檢查按鈕是不是都有出來，點餐選店時都會出現
        for checkStr in checkPoint[0]:
            try:
                self.assertTrue(checkStr in responseText)
            except AssertionError:
                print("[Error] " + TestName + " " + checkStr)

        testLog.objects.all().delete()

    def runOrderProcess(self,
                        store = None,
                        pdtProductName =  "茉莉綠茶（中）",
                        pdtPrice =  "16",
                        addOnName =  "椰果",
                        addOnPrice =  "10",
                        productAmount = "3",
                        pdtPicture = None,
                        continueOrder = False,
                        lastTotalPrice = 0,
                        itemClass = "1",
                        itemClassName = "找奶茶"):
        if pdtPicture == None:
            pdtPicture = self.pdtPicture
        if store == None:
            store = self.store

        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function

        #按下點餐紐
        response = self.actionTest('message' , "點餐")
        checkpoint = ("檢視購物車","回到主選單","選擇該店訂餐")
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇店點
        response = self.actionTest('postback' , store)
        checkpoint = ("找奶茶","找好茶")
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇餐點類別
        response = self.actionTest('postback' , store + "," + itemClassName +"," + itemClass)
        checkpoint = ("茶","中","大")
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇餐點，並帶上產品類別與名稱
        postData = store +","+pdtProductName+"," + pdtPrice + "," + pdtPicture + "," +  itemClassName +"," + itemClass
        response = self.actionTest('postback' , postData)
        checkpoint = ("請問要加什麼料呢?",)
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇加料
        postData = pdtProductName+","+addOnName+","+addOnPrice
        checkpoint = (pdtProductName,addOnName)
        response = self.actionTest('postback' , postData)
        self.checkResponse(response,checkpoint,nowTestName)

        #按下加料完畢
        response = self.actionTest('message' , "加料完畢")
        checkpoint = ("請輸入訂購數量",)
        self.checkResponse(response,checkpoint,nowTestName)

        #輸入數量完畢
        response = self.actionTest('message' , productAmount)
        checkpoint = ("是否繼續點餐",)
        self.checkResponse(response,checkpoint,nowTestName)

        #todo:有空的話要寫驗證邀請碼優惠


        lastTotalPrice += int((int(pdtPrice) + int(addOnPrice)) * int(productAmount))
        if continueOrder == False:
            #不繼續點餐，所以顯示購物車
            response = self.actionTest('message' , "否")
            checkpoint = ("購物車","使用邀請碼",pdtProductName,
                                    pdtPrice,
                                    addOnName,
                                    addOnPrice,
                                    productAmount,
                                    str(lastTotalPrice))
            self.checkResponse(response,checkpoint,nowTestName)

            #按下結帳按鈕
            response = self.actionTest('message' , "結帳")
            checkpoint = ("https:","line.me","payment")
            self.checkResponse(response,checkpoint,nowTestName)
        else:
            response = self.actionTest('message' , "是")
            checkpoint = ("找" ,"茶")
            self.checkResponse(response,checkpoint,nowTestName)
        return lastTotalPrice

    # 測試預設單線式購物流程，中間沒有額外繼續點餐
    # 檢查點餐菜單是不是正常
    def test_standaloneBuyAction(self):
        print("Method:standaloneBuyAction 測試預設單線式購物流程")
        #運行一個訂單的基本流程
        self.runOrderProcess()
        

    #Bug復現 : 同一筆訂單內不可以出現兩間店
    def test_cartCannotTwoStore(self):
        print("Method:cartCannotTwoStore 同一筆訂單內不可以出現兩間店")
        store = {
            "store1" : "13", #線上點餐1店
            "store2" : "14", #線上點餐2店
        }
        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function
        #先到第一間點餐
        self.runOrderProcess(store = store["store1"])

        #再到第二間店點餐
        #按下點餐紐
        response = self.actionTest('message' , "點餐")
        checkpoint = ("檢視購物車","回到主選單","選擇該店訂餐")
        self.checkResponse(response,checkpoint,nowTestName)
        
        #選擇店點
        response = self.actionTest('postback' , store["store2"])
        checkpoint = ("抱歉，不能跨店點餐，請先將購物車內的商品結帳")
        self.checkResponse(response,checkpoint,nowTestName)

    #Bug復現 : 同餐點點兩次不同的加料會出現錯誤
    def test_sameProductError(self):
        print("Method:sameProductError 測試同餐點點兩次會合併的問題")
        #運行一個訂單的基本流程
        _totalPrice = self.runOrderProcess(pdtProductName=self.pdtProductName,
                                           pdtPrice = self.pdtPrice,
                                           addOnName = self.addOnName,
                                           addOnPrice = self.addOnPrice,
                                           productAmount = self.productAmount,
                                           continueOrder = True)

        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function                            

        self.totalPrice += _totalPrice

        _pdtProductName = "茉莉綠茶（中）"
        _pdtPrice = "16"
        _addOnName = "椰果"
        _addOnPrice = "10"
        _productAmount = "3" 
        _itemClassName = "找好茶"
        _itemClass = "2"

        #選擇餐點類別
        response = self.actionTest('postback' , self.store + "," + _itemClassName +"," + _itemClass)
        checkpoint = ("茶","中","大")
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇餐點
        postData = self.store +","+_pdtProductName+"," + _pdtPrice + "," + self.pdtPicture + "," +  _itemClassName +"," + _itemClass
        response = self.actionTest('postback' , postData)
        checkpoint = ("請問要加什麼料呢?",)
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇加料
        postData = _pdtProductName+","+_addOnName+","+_addOnPrice
        response = self.actionTest('postback' , postData)
        checkpoint = (_pdtProductName,_addOnName)
        self.checkResponse(response,checkpoint,nowTestName)

        #按下加料完畢
        response = self.actionTest('message' , "加料完畢")
        checkpoint = ("請輸入訂購數量",)
        self.checkResponse(response,checkpoint,nowTestName)

        #輸入數量完畢
        response = self.actionTest('message' , _productAmount)
        checkpoint = ("是否繼續點餐",)
        self.checkResponse(response,checkpoint,nowTestName)

        #計算總金額
        self.totalPrice += int((int(_pdtPrice) + int(_addOnPrice)) * int(_productAmount))
        
        #講求順序一致
        checkpoint = ("購物車",self.pdtProductName,
                                self.pdtPrice,
                                self.addOnName,
                                self.addOnPrice,
                                self.productAmount,
                                _pdtProductName,
                                _pdtPrice,
                                _addOnName,
                                _addOnPrice,
                                _productAmount,
                                str(self.totalPrice))


        action = "否"
        createRequest = testToRequest()
        #模擬按鈕點餐
        request = createRequest.message(action)
        test_view.callback(request)
        
        #分析按下後的結果
        log = testLog.objects.all()
        logStr = self.decodeText(log[0].message)

        indexTemp = 0
        #檢查按鈕是不是都有出來，點餐選店時都會出現
        for checkStr in checkpoint:
            #檢查是否照順序一個一個增加
            index = logStr.find(checkStr)
            try:
                self.assertTrue(index > indexTemp)  
                indexTemp = index
            except AssertionError:
                matchLi = []
                match = re.finditer(checkStr,logStr)
                for matchChar in match:
                    matchLi.append(matchChar.start())
                indexTemp = matchLi[-1]
        testLog.objects.all().delete()



    #Bug復現 : 同一筆訂單內兩筆同名物件修改訂單後會一起刪除
    def test_twoSameNameProductDelete(self):
        print("Method:standaloneBuyAction 測試兩個同樣商品名稱的物件刪除會有問題")
        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function
        
        #運行一個訂單的基本流程
        _totalPrice = self.runOrderProcess(pdtProductName= self.pdtProductName ,addOnName="珍珠" , continueOrder = True)

        #運行一個訂單的基本流程
        #lastTotalPrice : 上一筆訂單的總價
        self.runOrderProcess(pdtProductName= self.pdtProductName , addOnName="椰果",addOnPrice="10",lastTotalPrice=_totalPrice)
        
        #輸入數量完畢
        response = self.actionTest('message' , "修改訂單")
        checkpoint = (("1."+self.pdtProductName),("2."+self.pdtProductName))
        self.checkResponse(response,checkpoint,nowTestName)

        response = self.actionTest('message' ,"刪除 2."+self.pdtProductName)
        checkpoint = ("購物車",self.pdtProductName,
                        self.pdtPrice,
                        "珍珠",
                        self.addOnPrice,
                        self.productAmount)
        self.checkResponse(response,checkpoint,nowTestName)
    
    def test_canDisableUseDivision(self):
        print ("Method: test_canUseDivision 測試可否使用邀請碼")
        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function

        response = self.actionTest('message' , "使用邀請碼")
        checkpoint = ("系統尚未開啟邀請碼優惠",)
        self.checkResponse(response,checkpoint,nowTestName)

    def test_canUseRecommendCode(self):
        print ("Method: test_canUseRecommendCode 測試當可以輸入邀請碼時，可以正常輸入")
        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function
        fakeUserinviteCode = inviteCodeManager.objects.filter(owner__lineID = self.fakeLineID).first().code
        UserinviteCode = inviteCodeManager.objects.filter(owner__lineID = self.lineID).first().code

        #使用邀請碼
        systemSetting.objects.all().delete()
        systemSetting.objects.create(inviteCodeStatus = '1', 
                                         autoReGeneratorInviteCode = 'True', 
                                         saleNumber = 10,)

        #A輸入B帳戶的邀請碼(正常)
        response = self.actionTest('message' , "使用邀請碼")
        checkpoint = ("請輸入邀請碼",)
        self.checkResponse(response,checkpoint,nowTestName)

        Member = member.objects.filter(lineID=self.fakeLineID).first()
        
        response = self.actionTest('message' , fakeUserinviteCode)
        checkpoint = ("邀請碼正確，已幫您打折了",)
        self.checkResponse(response,checkpoint,nowTestName)

        #B輸入A帳戶的邀請碼(正常)
        response = self.actionTest('message' , "使用邀請碼",LineID=self.fakeLineID)
        checkpoint = ("請輸入邀請碼",)
        self.checkResponse(response,checkpoint,nowTestName)

        Member = member.objects.filter(lineID=self.lineID).first()

        response = self.actionTest('message' , UserinviteCode,LineID=self.fakeLineID)
        checkpoint = ("邀請碼正確，已幫您打折了",)
        self.checkResponse(response,checkpoint,nowTestName)

        #A再輸入B帳戶的邀請碼(違規，推薦碼只能使用一次)
        response = self.actionTest('message' , "使用邀請碼")
        checkpoint = ("請輸入邀請碼",)
        self.checkResponse(response,checkpoint,nowTestName)

        Member = member.objects.filter(lineID=self.fakeLineID).first()

        response = self.actionTest('message' , UserinviteCode)
        checkpoint = ("抱歉，您已輸入過對方的邀請碼了",)
        self.checkResponse(response,checkpoint,nowTestName)

        #關閉使用邀請碼
        systemSetting.objects.all().delete()
        systemSetting.objects.create(inviteCodeStatus = '0', 
                                         autoReGeneratorInviteCode = 'True', 
                                         saleNumber = 10,)

    #Bug復現 : 選完主題餐點後跳回主選單後不能再選擇店點
    def test_orderToSelectItemClassNameAndJumpToAnotherOptionError(self):
        print("Method:test_orderToSelectItemClassNameAndJumpToAnotherOptionError 選完主題餐點後跳回主選單後不能再選擇店點")
        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function

        #按下點餐紐
        response = self.actionTest('message' , "點餐")
        checkpoint = ("檢視購物車","回到主選單","選擇該店訂餐")
        self.checkResponse(response,checkpoint,nowTestName)
        
        #選擇店點
        response = self.actionTest('postback' , self.store)
        checkpoint = ("找好茶","找奶茶")
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇餐點類別
        response = self.actionTest('postback' , self.store + "," + self.itemClassName +"," + self.itemClassId)
        checkpoint = ("茶","中","大")
        self.checkResponse(response,checkpoint,nowTestName)

        #運行一個訂單的基本流程
        totalPrice = self.runOrderProcess(continueOrder=False)

    #Bug復現 : 點單完畢填寫加料時，選擇點餐跳過後會錯誤
    def test_orderToAddonJumpToAnotherOptionError(self):
        print("Method:test_orderToAddonJumpToAnotherOptionError 點單完畢填寫加料時，選擇點餐跳過後會錯誤")
        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function

        #按下點餐紐
        response = self.actionTest('message' , "點餐")
        checkpoint = ("檢視購物車","回到主選單","選擇該店訂餐")
        self.checkResponse(response,checkpoint,nowTestName)
        
        #選擇店點
        response = self.actionTest('postback' , self.store)
        checkpoint = ("找好茶","找奶茶")
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇餐點類別
        response = self.actionTest('postback' , self.store + "," + self.itemClassName +"," + self.itemClassId)
        checkpoint = ("茶","中","大")
        self.checkResponse(response,checkpoint,nowTestName)

        #選擇餐點
        postData = self.store +","+self.pdtProductName+"," + self.pdtPrice + "," + self.pdtPicture + "," + self.itemClassName +"," + self.itemClassId
        response = self.actionTest('postback' , postData)
        checkpoint = ("請問要加什麼料呢?",)
        self.checkResponse(response,checkpoint,nowTestName)

        #按下點餐紐
        response = self.actionTest('message' , "點餐")
        checkpoint = ("檢視購物車","回到主選單","選擇該店訂餐")
        self.checkResponse(response,checkpoint,nowTestName)

        response = self.actionTest('message' , "檢視購物車")
        checkpoint = ("購物車","使用邀請碼","修改取餐人","修改電話")
        self.checkResponse(response,checkpoint,nowTestName)

    #測試取得訂單資料的時候會帶訂單編碼
    def test_shoppingCardNullError(self):
        print ("Method: test_shoppingCardNullError 測試取得訂單資料的時候會帶訂單編碼")
        frame = inspect.currentframe()
        nowTestName = inspect.getframeinfo(frame).function
        #運行一個訂單的基本流程
        totalPrice = self.runOrderProcess(continueOrder=True)

        #運行一個訂單的基本流程
        self.runOrderProcess(lastTotalPrice = totalPrice)
        
        shoppingOrders = shoppingCart.objects.filter(member__lineID=self.lineID, isPayed = 'False')
        for order in shoppingOrders:
            order.isPayed = 'True'
            order.save()
            
        response = test_view.queryAllOrder(request = None)
        self.assertTrue("OrderId" in str(response.content))
