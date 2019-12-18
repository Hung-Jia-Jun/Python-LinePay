import barcode
from LinepayAPP.imgurUpload import *
#from imgurUpload import *

import os

def generatorBarCode(codeText):
    code = barcode.get_barcode_class('code128')
    barCode = None
    try:
        barCode = code(str(codeText),barcode.writer.ImageWriter())
    except:
        barCode = code(str(codeText),barcode.writer.ImageWriter)
    codePath = "barcode_" + str(codeText)
    barCode.save(codePath) 
    return codePath

def runAndGetURL(text):
    codePath = generatorBarCode(text)
    codePath = codePath + ".png"
    imageUrl = upload_photo(codePath)
    os.remove(codePath)
    return imageUrl
if __name__ == "__main__":
    imageUrl = runAndGetURL('e28c')
    print (imageUrl)
