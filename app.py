from flask import Flask, request, jsonify
from flask_cors import CORS
import nltk
import spacy
from transformers import pipeline
import requests
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")
sentiment_analyzer = pipeline("sentiment-analysis")

API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')
BASE_URL = "https://api.openweathermap.org/data/2.5/"

def get_icon_url(icon):
    return f"https://openweathermap.org/img/wn/{icon}@2x.png"

def get_current_temperature(lat, lon):
    url = f"{BASE_URL}weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        return {
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'name': data['name'],
            'icon': get_icon_url(data['weather'][0]['icon']),
            'description': data['weather'][0]['description']
        }
    else:
        return None

def get_forecast(lat, lon):
    url = f"{BASE_URL}forecast?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        forecasts = {}
        for item in data['list']:
            day_name = datetime.fromtimestamp(item['dt']).strftime('%A')
            if day_name not in forecasts:
                forecasts[day_name] = []
            forecasts[day_name].append({
                'datetime': datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d %H:%M'),
                'temp': item['main']['temp'],
                'humidity': item['main']['humidity'],
                'icon': get_icon_url(item['weather'][0]['icon']),
                'description': item['weather'][0]['description']
            })
        return forecasts, data['city']['name']
    else:
        return None, None

def get_weather_by_city(city_name):
    url = f"{BASE_URL}weather?q={city_name}&units=metric&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        return {
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'name': data['name'],
            'icon': get_icon_url(data['weather'][0]['icon']),
            'description': data['weather'][0]['description']
        }
    else:
        return None


def get_forecast_by_city(city_name):
    url = f"{BASE_URL}forecast?q={city_name}&units=metric&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        forecasts = {}
        for item in data['list']:
            day_name = datetime.fromtimestamp(item['dt']).strftime('%A')
            if day_name not in forecasts:
                forecasts[day_name] = []
            forecasts[day_name].append({
                'datetime': datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d %H:%M'),
                'temp': item['main']['temp'],
                'humidity': item['main']['humidity'],
                'icon': get_icon_url(item['weather'][0]['icon']),
                'description': item['weather'][0]['description']
            })
        return forecasts, data['city']['name']
    else:
        return None, None

def generate_recommendation(description):
    if 'rain' in description:
        return "It will rain, I recommend taking an umbrella."
    elif 'clear' in description:
        return "The weather is clear, you might want to wear sunglasses."
    elif 'snow' in description:
        return "It will snow, I recommend wearing warm clothes and boots."
    else:
        return "Weather seems normal, have a great day!"

def process_temperature_query(query, lat=None, lon=None, city_name=None):
    tokens = nltk.word_tokenize(query.lower())
    
    temp_keywords = ['weather','temperature', 'hot', 'cold', 'warm', 'cool']
    forecast_keywords = ['forecast', 'prediction', 'future']
    
    if any(keyword in tokens for keyword in temp_keywords + forecast_keywords):
        if any(keyword in tokens for keyword in forecast_keywords):
            if lat is not None and lon is not None and city_name == '':
                forecast, location = get_forecast(lat, lon)
            elif lat is not None and lon is not None and city_name is not None:
                forecast, location = get_forecast_by_city(city_name)
            else:
                return {"error": "Latitude and longitude are required for forecast queries."}
                
            if forecast and location:
                forecast_with_recommendations = {}
                for day, day_forecast in forecast.items():
                    forecast_with_recommendations[day] = []
                    for item in day_forecast:
                        recommendation = generate_recommendation(item['description'])
                        item['recommendation'] = recommendation
                        forecast_with_recommendations[day].append(item)
                return {
                    "type": "forecast",
                    "location": location,
                    "forecast": forecast_with_recommendations
                }
            else:
                return {"error": "Sorry, I couldn't retrieve the forecast for your location."}
        else:
            if lat is not None and lon is not None and city_name == '':
                current_weather = get_current_temperature(lat, lon)
            elif lat is not None and lon is not None and city_name is not None:
                current_weather = get_weather_by_city(city_name)
            else:
                return {"error": "Latitude and longitude or city name is required for temperature queries."}
                
            if current_weather:
                recommendation = generate_recommendation(current_weather['description'])
                current_weather['recommendation'] = recommendation
                return {
                    "type": "current",
                    "weather": current_weather
                }
            else:
                return {"error": "Sorry, I couldn't retrieve the current temperature for your location."}
    else:
        sentiment = sentiment_analyzer(query)[0]
        if sentiment['label'] == 'POSITIVE':
            return {"message": "Hello! How can I help you with weather information?"}
        else:
            return {"message": "I'm here to help with weather-related queries. Could you please ask about the temperature or forecast for your location?"}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    lat = data.get('lat')
    lon = data.get('lon')
    city_name = data.get('city_name')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    response = process_temperature_query(user_message, lat, lon, city_name)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
