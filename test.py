from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os
import certifi

mongopassword = os.getenv("MONGOPASS")
url = f"mongodb+srv://summerham22:{mongopassword}@cluster0.c1zjv.mongodb.net/"
client = MongoClient(url, tlsCAFile=certifi.where())
title = "[TEST] 패키지 예매권 테스트 B"
title = ''.join(char for char in title if char.isalnum() or ('가' <= char <= '힣'))

db = client.Test

db.Test.create_index([('title'),('start_date')],unique=True)

try:
    db.Test.insert_one({"title":title,"start_date":"2024-12-30","hosts":[{"site_id":1,"url":"www.abc.test"}]})
except DuplicateKeyError:
    previous_data = db.Test.find_one({"title":title,"start_date":"2024-12-30"})
    
    previous_data = previous_data["hosts"]
    previous_data.append({"site_id":2, "url":"www.test.cp,"})
    
    interparkData = db.Test.update_one({"title":title,"start_date":"2024-12-30"},{"$set":{"hosts":previous_data}})