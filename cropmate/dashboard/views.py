from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, SignupForm
from .models import CropRecommendation
import json
import os
import numpy as np
import pickle
from groq import Groq
import re
import requests
from datetime import datetime, timedelta


@login_required
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')


@login_required
def weather_view(request):
    city = request.GET.get('city', 'Lahore')
    
    weather_data = None
    forecast_data = None
    error_message = None
    
    city_coordinates = {
        'Karachi': {'lat': 24.8607, 'lon': 67.0011},
        'Lahore': {'lat': 31.5204, 'lon': 74.3587},
        'Islamabad': {'lat': 33.6844, 'lon': 73.0479},
        'Rawalpindi': {'lat': 33.5651, 'lon': 73.0169},
        'Faisalabad': {'lat': 31.4504, 'lon': 73.1350},
        'Multan': {'lat': 30.1575, 'lon': 71.5249},
        'Peshawar': {'lat': 34.0151, 'lon': 71.5249},
        'Quetta': {'lat': 30.1798, 'lon': 66.9750},
        'Sialkot': {'lat': 32.4945, 'lon': 74.5229},
        'Gujranwala': {'lat': 32.1877, 'lon': 74.1945},
        'Bahawalpur': {'lat': 29.3544, 'lon': 71.6911},
        'Sargodha': {'lat': 32.0836, 'lon': 72.6711},
        'Hyderabad': {'lat': 25.3792, 'lon': 68.3683},
        'Sukkur': {'lat': 27.7058, 'lon': 68.8574},
        'Sahiwal': {'lat': 30.6682, 'lon': 73.1114}
    }
    
    if city not in city_coordinates:
        error_message = f"City '{city}' not found. Please select from available cities."
    else:
        try:
            coords = city_coordinates[city]
            lat = coords['lat']
            lon = coords['lon']
            
            current_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&timezone=Asia/Karachi&forecast_days=7"
            
            response = requests.get(current_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current']
                daily = data['daily']
                
                weather_data = {
                    'city': city,
                    'country': 'PK',
                    'temp': round(current['temperature_2m'], 1),
                    'feels_like': round(current['apparent_temperature'], 1),
                    'pressure': round(current['pressure_msl'], 0),
                    'humidity': current['relative_humidity_2m'],
                    'visibility': 10,
                    'wind_speed': round(current['wind_speed_10m'], 1),
                    'wind_deg': current['wind_direction_10m'],
                    'wind_dir': get_wind_direction(current['wind_direction_10m']),
                    'clouds': current['cloud_cover'],
                    'condition': get_weather_condition(current['weather_code']),
                    'description': get_weather_description(current['weather_code']),
                    'icon': get_weather_icon(current['weather_code']),
                    'rain_1h': round(current['precipitation'], 1),
                    'dt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                
                forecast_data = []
                for i in range(7):
                    forecast_data.append({
                        'date': daily['time'][i],
                        'day_name': datetime.strptime(daily['time'][i], '%Y-%m-%d').strftime('%A'),
                        'day_short': datetime.strptime(daily['time'][i], '%Y-%m-%d').strftime('%a'),
                        'temp_max': round(daily['temperature_2m_max'][i], 1),
                        'temp_min': round(daily['temperature_2m_min'][i], 1),
                        'temp_avg': round((daily['temperature_2m_max'][i] + daily['temperature_2m_min'][i]) / 2, 1),
                        'condition': get_weather_condition(daily['weather_code'][i]),
                        'rain': round(daily['precipitation_sum'][i], 1),
                        'wind_speed_avg': round(daily['wind_speed_10m_max'][i], 1),
                        'humidity_avg': 0,
                        'icon': get_weather_icon(daily['weather_code'][i])
                    })
                
                precipitation_chart = []
                for i in range(min(7, len(daily['time']))):
                    precipitation_chart.append({
                        'time': datetime.strptime(daily['time'][i], '%Y-%m-%d').strftime('%a'),
                        'rain': daily['precipitation_sum'][i],
                        'pop': daily['precipitation_probability_max'][i] if daily['precipitation_probability_max'][i] else 0
                    })
                
                total_rain_week = sum(daily['precipitation_sum'])
                weather_data['precipitation_chart'] = precipitation_chart
                weather_data['total_rain_today'] = round(daily['precipitation_sum'][0], 1)
                weather_data['rain_probability'] = round(daily['precipitation_probability_max'][0], 1) if daily['precipitation_probability_max'][0] else 0
                weather_data['total_rain_week'] = round(total_rain_week, 1)
                
            else:
                error_message = "Unable to fetch weather data. Please try again."
                
        except requests.exceptions.Timeout:
            error_message = "Weather service is taking too long to respond. Please try again."
        except requests.exceptions.RequestException:
            error_message = "Unable to fetch weather data. Please check your connection."
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
    
    popular_cities = [
        'Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad', 
        'Multan', 'Peshawar', 'Quetta', 'Sialkot', 'Gujranwala',
        'Bahawalpur', 'Sargodha', 'Hyderabad', 'Sukkur', 'Sahiwal'
    ]
    
    context = {
        'weather_data': weather_data,
        'forecast_data': forecast_data,
        'popular_cities': popular_cities,
        'selected_city': city,
        'error_message': error_message,
        'precipitation_chart_json': json.dumps(weather_data.get('precipitation_chart', [])) if weather_data else '[]'
    }
    
    return render(request, 'dashboard/weather.html', context)


def get_weather_condition(code):
    conditions = {
        0: 'Clear', 1: 'Mainly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
        45: 'Foggy', 48: 'Foggy', 51: 'Drizzle', 53: 'Drizzle', 55: 'Drizzle',
        61: 'Rain', 63: 'Rain', 65: 'Heavy Rain', 71: 'Snow', 73: 'Snow', 75: 'Snow',
        77: 'Snow', 80: 'Rain Showers', 81: 'Rain Showers', 82: 'Heavy Rain',
        85: 'Snow', 86: 'Snow', 95: 'Thunderstorm', 96: 'Thunderstorm', 99: 'Thunderstorm'
    }
    return conditions.get(code, 'Clear')


def get_weather_description(code):
    descriptions = {
        0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
        45: 'Fog', 48: 'Depositing rime fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
        55: 'Dense drizzle', 61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
        71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow', 77: 'Snow grains',
        80: 'Slight rain showers', 81: 'Moderate rain showers', 82: 'Violent rain showers',
        85: 'Slight snow showers', 86: 'Heavy snow showers', 95: 'Thunderstorm',
        96: 'Thunderstorm with hail', 99: 'Thunderstorm with heavy hail'
    }
    return descriptions.get(code, 'Clear sky')


def get_weather_icon(code):
    icons = {
        0: '01d', 1: '02d', 2: '03d', 3: '04d',
        45: '50d', 48: '50d', 51: '09d', 53: '09d', 55: '09d',
        61: '10d', 63: '10d', 65: '10d', 71: '13d', 73: '13d', 75: '13d',
        77: '13d', 80: '09d', 81: '09d', 82: '09d',
        85: '13d', 86: '13d', 95: '11d', 96: '11d', 99: '11d'
    }
    return icons.get(code, '01d')


def get_wind_direction(degree):
    if degree is None:
        return 'N/A'
    
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = round(degree / 22.5) % 16
    return directions[index]


@login_required
def sensors_view(request):
    return render(request, 'dashboard/sensors.html')


@login_required
def agronomist_view(request):
    return render(request, 'dashboard/agronomist.html')


@login_required
@require_http_methods(["POST"])
def ask_agronomist(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'success': False, 'error': 'No message provided'})

        try:
            client = Groq(
                api_key="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"
            )
            
            system_prompt = """
You are a professional agronomist. Your only role is to give clear, practical, agriculture-focused advice. Always answer directly, briefly, and to the point. Do not give generic suggestions such as “contact your local expert,” “seek local advice,” or “consult professionals.” Provide the best possible farming guidance using your own knowledge.

You must stay strictly on farming topics: crops, soil health, fertilizers, irrigation, pests, climate, yield improvement, and farm management. When the user goes off-topic, politely redirect them back to agriculture.

Your responses must follow these rules:

Short and concise

Contains only the essential information

Always relevant to farming

Friendly and professional

No emojis or decorative symbols

No unnecessary storytelling, small talk, or disclaimers

Do not refer the user to local offices or third-party experts

Examples

User: How can you help me?
Assistant: I can help you with crop advice, soil improvement, fertilizer planning, pest control, irrigation methods, and practical steps to improve your farm. Tell me what crop or issue you want to focus on.

User: What fertilizer should I use for wheat?
Assistant: Apply a balanced NPK, typically around 60–80 kg nitrogen, 30–40 kg phosphorus, and 20–25 kg potassium per hectare. Adjust based on soil tests.

User: Tell me a story.
Assistant: I focus on farming topics. If you want, I can explain how a farmer improves soil health or increases yield.




            """

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.8,
                max_tokens=200
            )
            
            ai_response = chat_completion.choices[0].message.content
            cleaned_response = clean_ai_response(ai_response)
            
            return JsonResponse({
                'success': True,
                'response': cleaned_response
            })
            
        except Exception as groq_error:
            fallback_response = get_expert_fallback(user_message)
            return JsonResponse({
                'success': True,
                'response': fallback_response
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Unable to process your request. Please try again.'
        })


def clean_ai_response(response):

    
    # Remove markdown formatting (asterisks, hashtags, backticks)
    cleaned = re.sub(r'\*+', '', response)
    cleaned = re.sub(r'#+\s*', '', cleaned)
    cleaned = re.sub(r'`+', '', cleaned)
    
    # Replace bullet points with numbers or remove them
    cleaned = re.sub(r'^\s*[•●◦▪▫-]\s+', '', cleaned, flags=re.MULTILINE)
    
    # Clean up excessive whitespace
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    # Preserve line breaks but clean up
    lines = [line.strip() for line in cleaned.split('\n')]
    cleaned = '\n'.join(lines)
    
    return cleaned.strip()


def get_expert_fallback(user_message):
    message_lower = user_message.lower()
    
    greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy', 'sup', 'what\'s up']
    if any(greeting in message_lower for greeting in greetings):
        return """Hey there! Great to see you. I'm here and ready to help with whatever you're growing. Whether it's pest problems keeping you up at night or you're planning your dream garden, I've got your back. What's on your mind today?"""
    
    thanks = ['thank', 'thanks', 'appreciate', 'helpful']
    if any(word in message_lower for word in thanks):
        return """You're very welcome! That's what I'm here for. Happy to help anytime you need farming advice. Good luck out there, and don't hesitate to ask if something else comes up!"""
    

    if 'how are you' in message_lower or 'how r u' in message_lower:
        return """I'm doing great, thanks for asking! Always excited when farmers stop by for advice. How are things going with your crops? Anything I can help you with today?"""
    
    expert_responses = {
        'crop': """Good question! Start by testing your soil - it tells you what'll grow best. Tomatoes, lettuce, peppers, and herbs are solid choices for most climates and beginners love them. Consider your local frost dates and market demand too. My advice? Start small, see what thrives, then expand. What's your growing zone?""",
        
        'soil': """Ah, soil - the foundation of everything! Here's the deal: add 2-3 inches of compost yearly, test your pH (shoot for 6.0-7.0), and use cover crops in the off-season. Mulch helps too. Good soil should feel alive in your hands - dark, crumbly, full of life. Give it some love and it'll give back tenfold!""",
        
        'pest': """Pests are frustrating, I get it! Best defense is good offense - use resistant varieties and give plants proper spacing. Check weekly to catch problems early. Ladybugs and lacewings are nature's pest control (and they work for free!). Try neem oil or insecticidal soap before going chemical. What pests are you dealing with?""",
        
        'water': """Great question! Water in early morning (6-8 AM) - less evaporation, plants get moisture for the day. Deep watering 2-3 times weekly beats daily sprinkles every time. Stick your finger in the soil 2-3 inches deep - dry? Water it. Mulch is your friend here, saves so much water. What are you growing?""",
        
        'fertilizer': """Smart to ask before feeding! Test your soil first - no point adding what you already have. Balanced 10-10-10 works for general feeding. Apply at planting and monthly during growing. Love organic? Try compost, aged manure, or fish emulsion. Remember: more isn't better - over-fertilizing burns plants and pollutes water.""",
        
        'plant': """Planting time! Choose healthy transplants or quality seeds. Depth and spacing matter - crowded plants fight for resources. Water well after planting and keep soil moist until they settle in. Mulch helps retain moisture and keeps weeds down. Check on them regularly for pests or diseases. First time planting?""",
        
        'weather': """Weather - the thing we can't control but always talk about! Check your local forecast and frost dates before planting. Most crops need consistent temps for germination. Too hot? Provide shade cloth. Too cold? Use row covers or cold frames. What's your weather throwing at you right now?"""
    }
    

    for keyword, response in expert_responses.items():
        if keyword in message_lower:
            return response
    
    return """That's an interesting question! For the most accurate advice for your specific situation, I'd recommend contacting your local agricultural extension office - they know your area's quirks better than anyone. They offer free soil testing too! In the meantime, what specific challenge are you facing? The more details you share, the better I can help!"""


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('dashboard:dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'dashboard/login.html', {'form': form})


def signup_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}! Please log in.')
            return redirect('root')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()
    
    return render(request, 'dashboard/signup.html', {'form': form})


def logout_view(request):

    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'You have been successfully logged out, {username}.')
    
    return redirect('root')


@login_required
def recommendations_view(request):

    prediction_result = None
    input_data = {}
    
    if request.method == 'POST':
        try:
            # Get form data
            nitrogen_val = request.POST.get('nitrogen', '').strip()
            phosphorus_val = request.POST.get('phosphorus', '').strip()
            potassium_val = request.POST.get('potassium', '').strip()
            temperature_val = request.POST.get('temperature', '').strip()
            humidity_val = request.POST.get('humidity', '').strip()
            ph_val = request.POST.get('ph', '').strip()
            rainfall_val = request.POST.get('rainfall', '').strip()
            
            # Validate all fields are filled
            if not all([nitrogen_val, phosphorus_val, potassium_val, temperature_val, humidity_val, ph_val, rainfall_val]):
                messages.error(request, 'Please fill in all fields.')
                return redirect('dashboard:recommendations')
            
            # Convert to float
            nitrogen = float(nitrogen_val)
            phosphorus = float(phosphorus_val)
            potassium = float(potassium_val)
            temperature = float(temperature_val)
            humidity = float(humidity_val)
            ph = float(ph_val)
            rainfall = float(rainfall_val)
            
            # Store input data for display
            input_data = {
                'nitrogen': nitrogen,
                'phosphorus': phosphorus,
                'potassium': potassium,
                'temperature': temperature,
                'humidity': humidity,
                'ph': ph,
                'rainfall': rainfall
            }
            
            # Prepare features for prediction
            feature_list = [nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]
            
            # Load the pickle models
            model_path = os.path.join(os.path.dirname(__file__), 'ml_models', 'model.pkl')
            scaler_path = os.path.join(os.path.dirname(__file__), 'ml_models', 'standscaler.pkl')
            minmax_path = os.path.join(os.path.dirname(__file__), 'ml_models', 'minmaxscaler.pkl')
            
            model = pickle.load(open(model_path, 'rb'))
            sc = pickle.load(open(scaler_path, 'rb'))
            ms = pickle.load(open(minmax_path, 'rb'))
            
            # Make prediction
            single_pred = np.array(feature_list).reshape(1, -1)
            scaled_features = ms.transform(single_pred)
            final_features = sc.transform(scaled_features)
            prediction = model.predict(final_features)
            
            # Crop dictionary
            crop_dict = {
                1: "Rice", 2: "Maize", 3: "Jute", 4: "Cotton", 5: "Coconut", 
                6: "Papaya", 7: "Orange", 8: "Apple", 9: "Muskmelon", 10: "Watermelon", 
                11: "Grapes", 12: "Mango", 13: "Banana", 14: "Pomegranate", 15: "Lentil", 
                16: "Blackgram", 17: "Mungbean", 18: "Mothbeans", 19: "Pigeonpeas", 
                20: "Kidneybeans", 21: "Chickpea", 22: "Coffee"
            }
            
            if prediction[0] in crop_dict:
                crop = crop_dict[prediction[0]]
                prediction_result = f"{crop} is the best crop to be cultivated with these conditions"
                
                # Save recommendation to database
                CropRecommendation.objects.create(
                    user=request.user,
                    nitrogen=nitrogen,
                    phosphorus=phosphorus,
                    potassium=potassium,
                    temperature=temperature,
                    humidity=humidity,
                    ph=ph,
                    rainfall=rainfall,
                    recommended_crop=crop
                )
                
                messages.success(request, f'Recommendation: {crop}')
            else:
                prediction_result = "Sorry, we could not determine the best crop with the provided data."
                messages.warning(request, 'Could not determine best crop')
                
        except ValueError as e:
            messages.error(request, 'Please fill in all fields with valid numbers.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    

    recent_recommendations = CropRecommendation.objects.filter(user=request.user)[:5]
    
    context = {
        'prediction_result': prediction_result,
        'input_data': input_data,
        'recent_recommendations': recent_recommendations
    }
    
    return render(request, 'dashboard/recommendations.html', context)


@login_required
def settings_view(request):
  
    return render(request, 'dashboard/settings.html')


@login_required
def update_profile(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        try:
            user = request.user
            
            
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, 'Username already exists. Please choose a different one.')
                return redirect('dashboard:settings')
            
   
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, 'Email already exists. Please use a different email.')
                return redirect('dashboard:settings')
            

            user.username = username
            user.email = email
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return redirect('dashboard:settings')


@login_required
@login_required
def change_password(request):

    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        user = request.user
        

        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            return redirect('dashboard:settings')
        

        if len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('dashboard:settings')
        

        user.set_password(new_password1)
        user.save()
        
        # Re-authenticate user to maintain session
        user = authenticate(username=user.username, password=new_password1)
        if user:
            login(request, user)
        
        messages.success(request, 'Password changed successfully!')
    
    return redirect('dashboard:settings')
