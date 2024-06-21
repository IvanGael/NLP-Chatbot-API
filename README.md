## NLP weather Chatbot API

A NLP project leveraging NLTK for extracting weather data.
Accurate weather data is retrieved from openweathermap api.

### Requirements

````
pip install -r requirements
````

````
python -m spacy download en_core_web_sm
````

Set up environment variables:
- Create a `.env` file
- Add your OpenWeatherMap API key:
  ```
  OPENWEATHERMAP_API_KEY=your_api_key_here
  ```

### Run

````
py app.py
````