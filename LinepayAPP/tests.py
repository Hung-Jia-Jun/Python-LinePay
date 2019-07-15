from django.test import TestCase
import views as test_view
import fetchWebServiceData as test_fetchWebServiceData
import pdb
from LinepayAPP.models import *
import LinepayAPP.CarouselTemplateGenerator as CarouselTemplateGenerator


class TestNahooClass(TestCase):
    @classmethod
	#執行下面的method之前，會先執行一次setUpTestData(self)來新增假資料
    def setUpTestData(self):
        self.classNahoo = test_fetchWebServiceData.nahoo()

    def test_shopInfo(self):
        print ('Method:shopInfo 查詢門店資料')
        shopInfo = self.classNahoo.shopInfo('13')
        self.assertEquals(shopInfo["shpShopName"] , '線上點餐1店')

    def test_queryHqInfoIds(self):
        print ('Method:queryHqInfoIds 查詢所有總部資料')
        QueryHqInfoIds = self.classNahoo.queryHqInfoIds()
        self.assertEquals(QueryHqInfoIds[3] , 75)

    def test_queryShopIds(self):
        print ('Method:queryShopIds 查詢所有總部下的門市資料')
        HqIds = self.classNahoo.queryHqInfoIds()
        QueryShopIds = []
        for hq in HqIds:
            QueryShopIds.append(self.classNahoo.queryShopIds(hq))
        self.assertTrue(QueryShopIds, None)

    def test_returnWebMenuData(self):
        print ('Method:returnWebMenuData 查詢門店菜單')
        shopId = 13 
        menu = self.classNahoo.returnWebMenuData(shopId)
        drinkTaiwanPrice = menu["products"][0]["pdtPriceTw"]
        self.assertEquals(drinkTaiwanPrice , 20)


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
        self.memberAction = test_view.memberAction(self.lineID,displayName = self.display_name)
        setMemberPhone = member(lineID=self.lineID,phone = self.phone,displayName = self.display_name)
        setMemberPhone.save()

        setClientSession = clientSession(member = setMemberPhone,status = 'default')
        setClientSession.save()
        
        return self
    def test_RealMember(self):
        print("Method:isMember 真實會員資料")
        self.assertTrue(test_view.isMember(self.lineID))
    
    def test_FakeMember(self):
        print("Method:isMember 非會員資料")
        self.assertFalse(test_view.isMember(self.fakeLineID))

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
        self.assertEqual(memberInfo.status ,'default')
        
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
        Cart = test_view.addCart(self.lineID , 2 , itemName , 22)
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

    def test_orderInfoFlex(self):
        print ('Method:carouselTemplate 檢查購物車發給客戶的訊息')
        response , content = self.LineMessage.orderInfoFlex(self.lineID,self.display_name,self.phone,self.address)
        self.assertEqual(response , None)
        self.assertEqual(content[0]['contents'][0]['text'] , '姓名')