from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import random
import json
import pymongo
from bson import ObjectId

app = Flask(__name__)

client = pymongo.MongoClient("mongodb+srv://lakhwanus009:MqLqLwDq79sOBZjh@cluster0.3qimy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["trending_db"]
collection = db["trends"]

def setup_driver():
    driver = webdriver.Chrome()
    return driver

def get_random_proxy():
    with open('proxies.txt', 'r') as f:
        proxies = f.readlines()
    return random.choice(proxies).strip()

def fetch_trending_topics():
    driver = setup_driver()
    result_dict = {}
    try:
        driver.get("https://x.com/login")

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='text']"))
        ).send_keys("upenderlakhwan")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
        ).click()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
        ).send_keys("Upender9@")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
        ).click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='primaryColumn']"))
        )
        driver.get("https://x.com/explore/tabs/trending")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']"))
        )
        spans = driver.find_elements(By.TAG_NAME, "span")

        unwanted_keywords = ["What's happening", "Trending in India", "·", "show more"]
        filtered_spans = [span.text for span in spans if not any(keyword in span.text.lower() for keyword in unwanted_keywords)]
        filtered_data = [item for item in filtered_spans if item]
        entertainment_index = filtered_data.index('Entertainment')
        filtered_data = filtered_data[entertainment_index + 1:]

        i = 1
        temp = []
        for item in filtered_data[:20]:
            if item.isdigit() and temp:
                result_dict[i] = temp
                temp = []
                i += 1
            temp.append(item)

        if temp:
            result_dict[i] = temp

    finally:
        driver.quit()

    # print("Result Dict:\n", result_dict)
    trends_data = {}
    for index, trend in result_dict.items():
        trends_data[f"nameoftrend{index}"] = trend[2]

    collection.insert_one({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trends": trends_data
    })

    return trends_data

def mongo_json_serializer(obj):
    if isinstance(obj, ObjectId):
        return str(obj) 
    raise TypeError(f"Type {type(obj)} not serializable")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script')
def run_script():
    trending_topics = fetch_trending_topics()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip_address = get_random_proxy()

    trend_names = [trend for trend in trending_topics.values()]
    # print(trending_topics)
    # print(trend_names)

    last_record = collection.find().sort("timestamp", -1).limit(1)
    json_record = {}

    for record in last_record:
        json_record = {
            "_id": str(record["_id"]), 
            "timestamp": record["timestamp"],
            **record["trends"]
        }

    json_record_str = json.dumps(json_record, default=mongo_json_serializer, indent=4)

    return render_template(
        'result.html',
        datetime=now,
        ip=ip_address,
        trends=trend_names,
        json_record=json_record_str
    )

if __name__ == '__main__':
    app.run(debug=True)
