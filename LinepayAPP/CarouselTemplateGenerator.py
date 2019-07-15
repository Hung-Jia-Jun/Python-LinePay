from linebot.models import *
from linebot import LineBotApi
from linebot import *
class Generator:
    def __init__(self):
        pass

    def PostbackAction(self,label,text,data):
        Action = PostbackTemplateAction(
                            label=label,
                            text=text,
                            data=data
                        )
        return Action 

    def MessageAction(self,label,text):
        Action = MessageTemplateAction(
                            label=label,
                            text=text
                        )
        return Action

    def URIAction(self,label,uri):
        Action = URITemplateAction(
                            label=label,
                            uri=uri
                        )
        return Action

    def carouselItem(self,thumbnail_image_url,title,text,action):
        Column = CarouselColumn(
                    thumbnail_image_url=thumbnail_image_url,
                    title=title,
                    text=text,
                    actions=action
                )
        return Column

    def chunks(self, l , n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def carouselTemplate(self,alt_text,CarouselList):
        Carousel_templateList = []
        columnChunk = self.chunks(CarouselList,10)
        for column in columnChunk:
            Carousel_templateList.append(TemplateSendMessage(
                    alt_text = alt_text,
                    template = CarouselTemplate(columns = column)
            ))
        return Carousel_templateList
