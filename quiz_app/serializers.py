from rest_framework import serializers
from .models import Quiz, Question, Choice, Category, UserQuizAttempt, UserAnswer

class CategorySerializer(serializers.ModelSerializer):
    quiz_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'color', 'quiz_count']

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'order']

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True, source='choice_set')
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 
            'explanation', 'marks', 'order', 'image', 'choices'
        ]

class QuizListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    question_count = serializers.ReadOnlyField()
    attempt_count = serializers.ReadOnlyField()
    average_score = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'category', 'difficulty',
            'time_limit', 'total_marks', 'question_count', 'attempt_count',
            'average_score', 'featured_image', 'ai_generated', 'ai_provider',
            'created_by_name', 'created_at'
        ]

class QuizDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True, source='question_set')
    question_count = serializers.ReadOnlyField()
    attempt_count = serializers.ReadOnlyField()
    average_score = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True)
    tag_list = serializers.ReadOnlyField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'category', 'difficulty',
            'time_limit', 'total_marks', 'pass_percentage', 'questions',
            'question_count', 'attempt_count', 'average_score',
            'featured_image', 'ai_generated', 'ai_provider', 'ai_prompt',
            'created_by_name', 'tag_list', 'created_at', 'updated_at'
        ]

class UserAnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    selected_choice = ChoiceSerializer(read_only=True)
    
    class Meta:
        model = UserAnswer
        fields = [
            'question', 'selected_choice', 'text_answer',
            'is_correct', 'marks_awarded', 'time_taken'
        ]

class UserQuizAttemptSerializer(serializers.ModelSerializer):
    quiz = QuizListSerializer(read_only=True)
    user_answers = UserAnswerSerializer(many=True, read_only=True, source='useranswer_set')
    percentage_score = serializers.ReadOnlyField()
    grade = serializers.ReadOnlyField()
    is_passed = serializers.ReadOnlyField()
    
    class Meta:
        model = UserQuizAttempt
        fields = [
            'id', 'quiz', 'status', 'score', 'percentage_score',
            'grade', 'is_passed', 'total_questions', 'correct_answers',
            'time_taken', 'started_at', 'completed_at', 'user_answers'
        ]
