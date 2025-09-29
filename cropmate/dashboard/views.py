from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, SignupForm
import json
import os
from groq import Groq


@login_required
def dashboard_view(request):
    """
    Renders the main dashboard page for CropMate application.
    Requires user to be logged in.
    """
    return render(request, 'dashboard/dashboard.html')


@login_required
def weather_view(request):
    """
    Renders the weather page for CropMate application.
    Integrates with Open-Meteo API for weather forecasting.
    Requires user to be logged in.
    """
    return render(request, 'dashboard/weather.html')


@login_required
def sensors_view(request):
    """
    Renders the sensor data page for CropMate application.
    Displays NPK levels, environmental conditions, and irrigation system status.
    Requires user to be logged in.
    """
    return render(request, 'dashboard/sensors.html')


@login_required
def agronomist_view(request):
    """
    Renders the virtual agronomist page for CropMate application.
    Provides AI-powered agricultural advice using Groq API.
    Requires user to be logged in.
    """
    return render(request, 'dashboard/agronomist.html')


@login_required
@require_http_methods(["POST"])
def ask_agronomist(request):
    """
    Handles AI agronomist questions using Groq API.
    Processes user questions and returns AI-generated agricultural advice.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'success': False, 'error': 'No message provided'})

        try:
            client = Groq(
                api_key="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"
            )
            
            # Concise agronomist system prompt
            system_prompt = """You are an expert agricultural advisor. Provide SHORT, PRACTICAL answers (50-80 words max).

RULES:
- Give direct, actionable advice only
- Use simple bullet points if needed
- Include specific numbers/measurements
- No long explanations or theory
- Focus on immediate solutions
- Be conversational and helpful

Example good response: "For tomatoes: Plant after last frost, space 18-24 inches apart, water deeply 2x weekly, use 10-10-10 fertilizer monthly. Stake plants when 12 inches tall."

Keep it SHORT and USEFUL."""

            # Make API call to Groq
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.5,
                max_tokens=150
            )
            
            ai_response = chat_completion.choices[0].message.content
            
            # Clean the response - remove special characters and formatting issues
            cleaned_response = clean_ai_response(ai_response)
            
            return JsonResponse({
                'success': True,
                'response': cleaned_response
            })
            
        except Exception as groq_error:
            # Fallback to expert knowledge base
            fallback_response = get_expert_fallback(user_message)
            return JsonResponse({
                'success': True,
                'response': fallback_response
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Unable to process your request at the moment. Please try again.'
        })


def clean_ai_response(response):
    """
    Clean AI response by removing unwanted characters and formatting
    """
    import re
    
    # Remove excessive asterisks, hashtags, and markdown formatting
    cleaned = re.sub(r'\*+', '', response)
    cleaned = re.sub(r'#+', '', cleaned)
    cleaned = re.sub(r'`+', '', cleaned)
    
    # Remove excessive newlines and spaces
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove emojis if present (optional)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", flags=re.UNICODE)
    cleaned = emoji_pattern.sub(r'', cleaned)
    
    # Clean up spacing and return clean response
    cleaned = cleaned.strip()
    return cleaned


def get_expert_fallback(user_message):
    """
    Provide expert agricultural advice when API is unavailable
    """
    message_lower = user_message.lower()
    
    expert_responses = {

        "you have to make short consise questions to the point not too much longer or boring"
    }
    expert_responses = {
        'crop': "Choose crops based on: • Local climate zone • Soil pH (test first) • Market demand. Start with: tomatoes, lettuce, herbs, peppers. These are beginner-friendly and profitable.",
        
        'soil': "Improve soil: • Add 2-3 inches compost yearly • Test pH (aim 6.0-7.0) • Use cover crops in winter • Mulch 3-4 inches • Avoid walking on wet soil.",
        
        'pest': "Pest control: • Check plants weekly • Use beneficial insects (ladybugs) • Try neem oil or soap spray first • Rotate crops yearly • Remove infected plants quickly.",
        
        'water': "Watering tips: • Early morning (6-8 AM) best • Deep water 2x weekly better than daily light watering • Check soil 2 inches deep first • Mulch reduces water needs 50%."
    },
    expert_responses = {

        'soil': """To improve soil health effectively:

• Organic Matter: Add 2-3 inches of well-aged compost annually
• Soil Testing: Test pH (optimal 6.0-7.0 for most crops) and nutrient levels every 2-3 years  
• Cover Crops: Plant nitrogen-fixing legumes during off-seasons
• Avoid Compaction: Use raised beds or permanent pathways to protect soil structure
• Mulching: Apply 2-4 inches of organic mulch to retain moisture and suppress weeds

Healthy soil should be dark, crumbly, and rich in organic matter. This foundation is crucial for productive, sustainable farming.""",

        'pest': """Integrated Pest Management (IPM) approach:

• Prevention First: Use resistant varieties, proper spacing, and crop rotation
• Regular Monitoring: Inspect plants weekly for early pest detection
• Beneficial Insects: Encourage ladybugs, lacewings, and parasitic wasps
• Organic Controls: Use neem oil, insecticidal soaps, or diatomaceous earth
• Physical Barriers: Row covers, copper tape, or sticky traps
• Last Resort: Use targeted pesticides only when necessary, following label instructions

Remember: A healthy ecosystem with diverse beneficial insects is your best long-term pest management strategy.""",

        'water': """Efficient irrigation guidelines:

• Timing: Water early morning (6-8 AM) to reduce evaporation and disease risk
• Deep Watering: Apply 1-2 inches weekly, watering deeply but less frequently
• Soil Check: Test moisture 2-3 inches deep before watering
• Mulch Benefits: Reduces water needs by 25-50% and maintains soil temperature
• Drip Systems: Most efficient method, delivering water directly to root zones
• Avoid Overhead: Sprinklers can promote fungal diseases on leaves

Monitor plants for stress signs: wilting, stunted growth, or leaf color changes. Adjust watering based on weather conditions and plant development stage."""
    }
    
    # Find best matching response
    for keyword, response in expert_responses.items():
        if keyword in message_lower:
            return response
    
    # Default expert response
    return "For your specific question: • Contact local extension office • Consider your climate/soil • Start with proven methods • Keep records of what works. Your county agent can provide region-specific guidance."


def login_view(request):
    """
    Handles user login with email and password.
    """
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
    """
    Handles user registration with username, email, password, and confirm password.
    """
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
    """
    Handles user logout and redirects to login page.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'You have been successfully logged out, {username}.')
    
    return redirect('root')
