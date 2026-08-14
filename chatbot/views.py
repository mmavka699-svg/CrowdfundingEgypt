import os
import json
import dotenv
from pathlib import Path
from google import genai
from google.genai import types
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import get_relevant_context

dotenv.load_dotenv()

SYSTEM_PROMPT = """You are a helpful assistant for "Crowdfunding Egypt", a donation platform in Egypt.
Context:
{context}
"""

@csrf_exempt
@require_POST
def chat(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        current_api_key = (
            getattr(settings, 'GOOGLE_API_KEY', None)
            or getattr(settings, 'GEMINI_API_KEY', None)
            or os.getenv('GOOGLE_API_KEY')
            or os.getenv('GEMINI_API_KEY')
        )
        if not current_api_key:
            return JsonResponse({'error': 'API key is missing or not configured in settings/environment.'}, status=500)

        client = genai.Client(api_key=current_api_key)

        context = get_relevant_context(user_message, user=request.user)
        system_prompt = SYSTEM_PROMPT.format(context=context)

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )

        return JsonResponse({'reply': response.text})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

