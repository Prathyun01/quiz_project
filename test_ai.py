import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from django.conf import settings
import requests

def test_perplexity():
    if not hasattr(settings, 'PERPLEXITY_API_KEY') or not settings.PERPLEXITY_API_KEY:
        print("❌ Perplexity API key not configured")
        return
        
    print(f"✅ Perplexity API key found: {settings.PERPLEXITY_API_KEY[:10]}...")
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Perplexity API working: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ Perplexity API error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Perplexity error: {e}")

def test_gemini():
    if not hasattr(settings, 'GOOGLE_API_KEY') or not settings.GOOGLE_API_KEY:
        print("❌ Google API key not configured")
        return
        
    try:
        import google.generativeai as genai
        print(f"✅ Google API key found: {settings.GOOGLE_API_KEY[:10]}...")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Use updated model name
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello")
        
        print(f"✅ Gemini API working: {response.text}")
    except Exception as e:
        print(f"❌ Gemini error: {e}")


if __name__ == "__main__":
    #print("=== Testing Available AI APIs ===\n")
    
    #print("Testing Perplexity AI:")
    #test_perplexity()
    
    print("\nTesting Gemini:")
    test_gemini()
    
    print("\n=== Summary ===")
    print("• Perplexity AI: Real-time search capabilities")
    print("• Google Gemini: Free alternative with good quality")
