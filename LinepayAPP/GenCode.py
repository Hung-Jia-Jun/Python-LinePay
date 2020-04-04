import uuid
import random
getPos = random.randint(5, 32)
password = uuid.uuid1().hex[getPos-4:getPos]