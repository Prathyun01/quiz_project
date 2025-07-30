import requests
import json
import logging
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional
import time
import hashlib
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DifficultyLevel(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

class AIProvider(Enum):
    GEMINI = 'gemini'
    PERPLEXITY = 'perplexity'

@dataclass
class QuizConfig:
    topic: str
    category: str
    difficulty: DifficultyLevel
    num_questions: int
    provider: AIProvider
    
    def to_cache_key(self) -> str:
        """Generate a cache key for this configuration"""
        content = f"{self.topic}_{self.category}_{self.difficulty.value}_{self.num_questions}_{self.provider.value}"
        return f"quiz_{hashlib.md5(content.encode()).hexdigest()}"

class QuizValidationError(Exception):
    """Custom exception for quiz validation errors"""
    pass

class AIQuizService:
    # Constants
    DEFAULT_TIMEOUT = 30
    TEST_TIMEOUT = 10
    CACHE_TTL = 3600  # 1 hour
    MAX_QUESTIONS = 50
    MIN_QUESTIONS = 1
    
    # API Configuration
    GEMINI_CONFIG = {
        'url_template': "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={}",
        'model': 'gemini-1.5-flash-latest',
        'max_tokens': 4000,
        'temperature': 0.7
    }
    
    PERPLEXITY_CONFIG = {
        'url': "https://api.perplexity.ai/chat/completions",
        'model': 'sonar-pro',
        'max_tokens': 2000,
        'temperature': 0.7
    }

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.gemini_available = self._check_api_key('GOOGLE_API_KEY')
        self.perplexity_available = self._check_api_key('PERPLEXITY_API_KEY')
        
        if not (self.gemini_available or self.perplexity_available):
            logger.warning("No AI providers available. Please configure API keys.")

    def _check_api_key(self, key_name: str) -> bool:
        """Check if API key is configured"""
        return hasattr(settings, key_name) and getattr(settings, key_name)

    def generate_quiz(self, topic: str, category: str, difficulty: str = 'medium',
                     num_questions: int = 10, provider: str = 'gemini') -> Dict:
        """Generate a complete quiz using AI with enhanced validation and caching"""
        
        # Validate inputs
        self._validate_inputs(topic, category, difficulty, num_questions, provider)
        
        # Create config object
        config = QuizConfig(
            topic=topic.strip(),
            category=category.strip(),
            difficulty=DifficultyLevel(difficulty),
            num_questions=num_questions,
            provider=AIProvider(provider)
        )
        
        # Check cache first
        if self.use_cache:
            cached_quiz = self._get_cached_quiz(config)
            if cached_quiz:
                logger.info(f"Returning cached quiz for {topic}")
                return cached_quiz

        start_time = time.time()
        logger.info(f"Generating quiz: {config}")

        try:
            # Generate quiz based on provider
            if config.provider == AIProvider.GEMINI:
                if not self.gemini_available:
                    raise QuizValidationError("Gemini service not available. Please check API key.")
                quiz_data = self._generate_quiz_gemini(config)
            else:  # PERPLEXITY
                if not self.perplexity_available:
                    raise QuizValidationError("Perplexity service not available. Please check API key.")
                quiz_data = self._generate_quiz_perplexity(config)

            # Add metadata
            generation_time = time.time() - start_time
            quiz_data['generation_metadata'] = {
                'provider': config.provider.value,
                'generation_time': round(generation_time, 2),
                'topic': config.topic,
                'category': config.category,
                'difficulty': config.difficulty.value,
                'generated_at': int(time.time()),
                'cached': False
            }

            # Cache the result
            if self.use_cache:
                self._cache_quiz(config, quiz_data)

            logger.info(f"Quiz generated successfully in {generation_time:.2f}s")
            return quiz_data

        except Exception as e:
            logger.error(f"Quiz generation failed: {str(e)}")
            # Return fallback quiz with error indication
            fallback_quiz = self._create_fallback_quiz(config)
            fallback_quiz['generation_metadata']['error'] = str(e)
            return fallback_quiz

    def _validate_inputs(self, topic: str, category: str, difficulty: str, 
                        num_questions: int, provider: str) -> None:
        """Validate input parameters"""
        if not topic or not topic.strip():
            raise QuizValidationError("Topic cannot be empty")
        
        if not category or not category.strip():
            raise QuizValidationError("Category cannot be empty")
        
        if difficulty not in [d.value for d in DifficultyLevel]:
            raise QuizValidationError(f"Invalid difficulty. Must be one of: {[d.value for d in DifficultyLevel]}")
        
        if not (self.MIN_QUESTIONS <= num_questions <= self.MAX_QUESTIONS):
            raise QuizValidationError(f"Number of questions must be between {self.MIN_QUESTIONS} and {self.MAX_QUESTIONS}")
        
        if provider not in [p.value for p in AIProvider]:
            raise QuizValidationError(f"Invalid provider. Must be one of: {[p.value for p in AIProvider]}")

    def _get_cached_quiz(self, config: QuizConfig) -> Optional[Dict]:
        """Retrieve quiz from cache"""
        try:
            cache_key = config.to_cache_key()
            cached_data = cache.get(cache_key)
            if cached_data:
                cached_data['generation_metadata']['cached'] = True
                return cached_data
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None

    def _cache_quiz(self, config: QuizConfig, quiz_data: Dict) -> None:
        """Store quiz in cache"""
        try:
            cache_key = config.to_cache_key()
            cache.set(cache_key, quiz_data, self.CACHE_TTL)
            logger.debug(f"Quiz cached with key: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _generate_quiz_gemini(self, prompt, num_questions):
        """Generate questions using Gemini with retry logic"""
        max_retries = 2
        base_delay = 5  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Gemini attempt {attempt + 1}/{max_retries + 1}")
                
                # Configure generation settings for better reliability
                generation_config = genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=2048,
                    candidate_count=1
                )
                
                # Generate content without request_options (not supported in this version)
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                questions_text = response.text.strip()
                
                # Clean JSON - Remove code block markers
                if questions_text.startswith('```json'):
                    questions_text = questions_text[7:]
                elif questions_text.startswith('```'):
                    questions_text = questions_text[3:]
                
                if questions_text.endswith('```'):
                    questions_text = questions_text[:-3]
                
                # Additional cleaning for common JSON issues
                questions_text = questions_text.strip()
                
                try:
                    questions = json.loads(questions_text)
                    if questions:  # If we got valid questions
                        return questions[:num_questions]
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Raw response: {questions_text}")
                    
                    # Try multiple JSON fixing strategies
                    try:
                        # Strategy 1: Fix common JSON issues line by line
                        lines = questions_text.split('\n')
                        fixed_lines = []
                        
                        for line in lines:
                            # Fix unquoted numbers in options
                            if '"A":' in line or '"B":' in line or '"C":' in line or '"D":' in line:
                                # Look for unquoted numbers after colons
                                import re
                                line = re.sub(r':\s*(\d+\.?\d*)\s*([,}])', r': "\1"\2', line)
                            fixed_lines.append(line)
                        
                        fixed_text = '\n'.join(fixed_lines)
                        questions = json.loads(fixed_text)
                        logger.info("Fixed JSON parsing using line-by-line strategy")
                        return questions[:num_questions]
                        
                    except Exception as e2:
                        logger.error(f"Line-by-line fix failed: {e2}")
                        
                        # Strategy 2: Try to extract valid JSON objects manually
                        try:
                            # Look for individual question objects
                            question_objects = []
                            import re
                            
                            # Find all complete question objects
                            pattern = r'\{[^{}]*"question"[^{}]*"options"[^{}]*\{[^{}]*\}[^{}]*"correct_answer"[^{}]*"explanation"[^{}]*\}'
                            matches = re.findall(pattern, questions_text, re.DOTALL)
                            
                            for match in matches[:num_questions]:
                                try:
                                    # Try to parse each question individually
                                    question_obj = json.loads(match)
                                    question_objects.append(question_obj)
                                except:
                                    continue
                            
                            if question_objects:
                                logger.info(f"Extracted {len(question_objects)} valid questions manually")
                                return question_objects
                                
                        except Exception as e3:
                            logger.error(f"Manual extraction failed: {e3}")
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a retryable error
                if any(keyword in error_msg for keyword in ['timeout', 'overloaded', '503', '504', 'deadline']):
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Gemini API retryable error: {e}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Gemini API failed after {max_retries + 1} attempts: {e}")
                        raise
                else:
                    # Non-retryable error
                    logger.error(f"Gemini API non-retryable error: {e}")
                    raise
        
        # If we get here, all retries failed
        return []

    def _generate_quiz_perplexity(self, config: QuizConfig) -> Dict:
        """Generate quiz using Perplexity AI with improved error handling"""
        prompt = self._create_quiz_prompt(config)

        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.PERPLEXITY_CONFIG['model'],
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert educational content creator. Generate high-quality, educational quizzes in valid JSON format only. Do not include any text outside the JSON response."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": self.PERPLEXITY_CONFIG['max_tokens'],
            "temperature": self.PERPLEXITY_CONFIG['temperature']
        }

        response = requests.post(
            self.PERPLEXITY_CONFIG['url'],
            headers=headers,
            json=data,
            timeout=self.DEFAULT_TIMEOUT
        )

        if response.status_code != 200:
            raise Exception(f"Perplexity API request failed: {response.status_code} - {response.text}")

        result = response.json()
        
        # Enhanced response validation
        if 'choices' not in result or not result['choices']:
            raise Exception("No choices in Perplexity API response")
        
        choice = result['choices'][0]
        if 'message' not in choice or 'content' not in choice['message']:
            raise Exception("Invalid response structure from Perplexity API")
        
        content = choice['message']['content']
        return self._parse_ai_response(content, config)

    def _create_quiz_prompt(self, config: QuizConfig) -> str:
        """Create detailed prompt for AI quiz generation with improved structure"""
        difficulty_descriptions = {
            DifficultyLevel.EASY: 'basic knowledge, fundamental concepts, and simple recall',
            DifficultyLevel.MEDIUM: 'intermediate understanding, application of concepts, and analysis',
            DifficultyLevel.HARD: 'advanced concepts, complex analysis, synthesis, and evaluation'
        }

        prompt = f"""
Create a {config.difficulty.value} difficulty quiz about "{config.topic}" in the {config.category} category with exactly {config.num_questions} multiple-choice questions.

REQUIREMENTS:
1. Each question must have exactly 4 answer choices labeled A, B, C, D
2. Only one choice should be correct per question
3. Include detailed explanations for correct answers (2-3 sentences minimum)
4. Questions should test {difficulty_descriptions[config.difficulty]}
5. Make questions clear, specific, and educationally valuable
6. Ensure answer choices are plausible and well-distributed
7. Avoid ambiguous wording and ensure each question has a single, clearly correct answer
8. Include variety in question types (factual, conceptual, application-based)

Return ONLY a valid JSON object with this exact structure (no additional text):
{{
    "title": "Engaging quiz title about {config.topic} (50-100 characters)",
    "description": "Clear description of what the quiz covers (100-300 characters)",
    "questions": [
        {{
            "question": "Clear, specific question text ending with a question mark?",
            "choices": [
                "Choice A - first option",
                "Choice B - second option", 
                "Choice C - third option",
                "Choice D - fourth option"
            ],
            "correct_answer": 1,
            "explanation": "Detailed explanation of why this answer is correct and why other options are incorrect."
        }}
    ]
}}

CRITICAL NOTES:
- correct_answer must be 1, 2, 3, or 4 (corresponding to choices A, B, C, D)
- All JSON must be properly formatted and valid
- No text outside the JSON object
- Questions must be unique and non-repetitive

Topic: {config.topic}
Category: {config.category}
Difficulty: {config.difficulty.value}
Number of questions: {config.num_questions}
"""
        return prompt

    def _parse_ai_response(self, response_text: str, config: QuizConfig) -> Dict:
        """Parse and validate AI response with enhanced error handling"""
        try:
            # Clean the response text
            cleaned_text = self._clean_response_text(response_text)
            
            # Parse JSON
            quiz_data = json.loads(cleaned_text)
            
            # Validate and enhance structure
            quiz_data = self._validate_and_enhance_quiz_data(quiz_data, config)
            
            logger.info(f"Successfully parsed quiz with {len(quiz_data['questions'])} questions")
            return quiz_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.debug(f"Failed to parse response: {response_text[:500]}...")
            return self._create_fallback_quiz(config)
        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            return self._create_fallback_quiz(config)

    def _clean_response_text(self, response_text: str) -> str:
        """Clean and extract JSON from AI response"""
        cleaned_text = response_text.strip()
        
        # Remove code block markers
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]
        
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        
        # Find JSON content
        start = cleaned_text.find('{')
        end = cleaned_text.rfind('}') + 1
        
        if start != -1 and end > start:
            return cleaned_text[start:end]
        
        return cleaned_text

    def _validate_and_enhance_quiz_data(self, quiz_data: Dict, config: QuizConfig) -> Dict:
        """Validate and enhance quiz data structure"""
        if 'questions' not in quiz_data:
            raise QuizValidationError("No questions found in response")
        
        # Ensure basic structure
        if 'title' not in quiz_data:
            quiz_data['title'] = f"{config.topic} Quiz ({config.difficulty.value.title()} Level)"
        if 'description' not in quiz_data:
            quiz_data['description'] = f"Test your knowledge of {config.topic} with this {config.difficulty.value} difficulty quiz."

        # Validate and fix questions
        validated_questions = []
        for i, q in enumerate(quiz_data['questions']):
            try:
                validated_q = self._validate_question(q, i + 1)
                validated_questions.append(validated_q)
            except Exception as e:
                logger.warning(f"Skipping invalid question {i + 1}: {e}")
                continue

        if not validated_questions:
            raise QuizValidationError("No valid questions found")

        quiz_data['questions'] = validated_questions
        return quiz_data

    def _validate_question(self, question: Dict, question_num: int) -> Dict:
        """Validate individual question structure"""
        required_fields = ['question', 'choices', 'correct_answer']
        
        for field in required_fields:
            if field not in question:
                raise QuizValidationError(f"Missing required field: {field}")

        # Validate question text
        if not question['question'].strip():
            raise QuizValidationError("Question text cannot be empty")

        # Ensure exactly 4 choices
        choices = question['choices']
        if not isinstance(choices, list):
            raise QuizValidationError("Choices must be a list")
        
        while len(choices) < 4:
            choices.append(f"Option {len(choices) + 1}")
        question['choices'] = choices[:4]

        # Validate correct_answer
        correct_answer = question['correct_answer']
        if not isinstance(correct_answer, int) or not (1 <= correct_answer <= 4):
            logger.warning(f"Invalid correct_answer for question {question_num}, defaulting to 1")
            question['correct_answer'] = 1

        # Ensure explanation exists
        if 'explanation' not in question or not question['explanation'].strip():
            question['explanation'] = "Explanation not provided."

        return question

    def _create_fallback_quiz(self, config: QuizConfig) -> Dict:
        """Create a fallback quiz when AI generation fails"""
        questions = []
        for i in range(min(config.num_questions, 5)):  # Limit fallback questions
            questions.append({
                'question': f"Sample question about {config.topic} #{i+1}: What is a key concept in {config.topic}?",
                'choices': [
                    f"Correct answer about {config.topic}",
                    f"Incorrect option A for {config.topic}", 
                    f"Incorrect option B for {config.topic}",
                    f"Incorrect option C for {config.topic}"
                ],
                'correct_answer': 1,
                'explanation': f"This is a sample explanation about {config.topic}. In a real quiz, this would contain detailed information about why this answer is correct."
            })

        return {
            'title': f"{config.topic} Quiz ({config.difficulty.value.title()} Level)",
            'description': f"A {config.difficulty.value} difficulty quiz about {config.topic} in the {config.category} category. Note: This is a fallback quiz due to AI generation issues.",
            'questions': questions,
            'generation_metadata': {
                'provider': config.provider.value,
                'generation_time': 0,
                'topic': config.topic,
                'category': config.category,
                'difficulty': config.difficulty.value,
                'generated_at': int(time.time()),
                'cached': False,
                'fallback': True
            }
        }

    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        providers = []
        if self.gemini_available:
            providers.append(AIProvider.GEMINI.value)
        if self.perplexity_available:
            providers.append(AIProvider.PERPLEXITY.value)
        return providers

    def test_connection(self, provider: str) -> Dict:
        """Test AI provider connection with timeout and enhanced error handling"""
        try:
            if provider == AIProvider.GEMINI.value and self.gemini_available:
                return self._test_gemini_connection()
            elif provider == AIProvider.PERPLEXITY.value and self.perplexity_available:
                return self._test_perplexity_connection()
            else:
                return {
                    'success': False, 
                    'message': f'Provider {provider} not available or not configured'
                }
        except Exception as e:
            logger.error(f"Connection test failed for {provider}: {e}")
            return {'success': False, 'message': f'Connection test failed: {str(e)}'}

    def _test_gemini_connection(self) -> Dict:
        """Test Gemini API connection"""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": "Respond with 'OK'"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            }
            url = self.GEMINI_CONFIG['url_template'].format(settings.GOOGLE_API_KEY)
            response = requests.post(url, headers=headers, json=data, timeout=self.TEST_TIMEOUT)
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Gemini API connection successful'}
            else:
                return {'success': False, 'message': f'Gemini API test failed: HTTP {response.status_code}'}
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Gemini API connection timeout'}
        except Exception as e:
            return {'success': False, 'message': f'Gemini connection error: {str(e)}'}

    def _test_perplexity_connection(self) -> Dict:
        """Test Perplexity API connection"""
        try:
            headers = {
                "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.PERPLEXITY_CONFIG['model'],
                "messages": [{"role": "user", "content": "Respond with 'OK'"}],
                "max_tokens": 10
            }
            response = requests.post(
                self.PERPLEXITY_CONFIG['url'],
                headers=headers,
                json=data,
                timeout=self.TEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Perplexity API connection successful'}
            else:
                return {'success': False, 'message': f'Perplexity API test failed: HTTP {response.status_code}'}
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Perplexity API connection timeout'}
        except Exception as e:
            return {'success': False, 'message': f'Perplexity connection error: {str(e)}'}

    def clear_cache(self, topic: str = None, category: str = None) -> Dict:
        """Clear quiz cache (optionally filtered by topic/category)"""
        try:
            if topic or category:
                # This would require a more sophisticated cache key pattern
                # For now, return a message about manual cache clearing
                return {
                    'success': False, 
                    'message': 'Selective cache clearing not implemented. Use Django cache management.'
                }
            else:
                cache.clear()
                return {'success': True, 'message': 'Quiz cache cleared successfully'}
        except Exception as e:
            return {'success': False, 'message': f'Cache clear failed: {str(e)}'}

    def get_quiz_stats(self) -> Dict:
        """Get service statistics"""
        return {
            'available_providers': self.get_available_providers(),
            'gemini_available': self.gemini_available,
            'perplexity_available': self.perplexity_available,
            'cache_enabled': self.use_cache,
            'supported_difficulties': [d.value for d in DifficultyLevel],
            'max_questions': self.MAX_QUESTIONS,
            'min_questions': self.MIN_QUESTIONS
        }