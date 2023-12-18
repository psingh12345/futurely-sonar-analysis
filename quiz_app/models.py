from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from ckeditor.fields import RichTextField

Person = get_user_model()

class TimeStampModel(models.Model):
    """TimeStamp Model"""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    modified_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True


class Quiz(TimeStampModel):
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True, default="")
    duration = models.IntegerField(default=0,help_text="Duration of the Quiz in minute")
    is_active = models.BooleanField(default=True)
    quiz_banner = models.FileField(upload_to='quiz',  null=True, blank=True)
    correct_answer_point = models.FloatField(default=0, help_text="point for each correct answer")
    deduction_answer_point = models.FloatField(default=0,help_text="deduction point for each incorrect answer")

    class Meta:
        verbose_name = '1.1 Quiz'
        verbose_name_plural = '1.1 Quizzes'

    def __str__(self):
        return f"{self.title}"


class QuizQuestion(TimeStampModel):
    QUESTION_TYPES = (
        ('Single Selection', 'Single Selection'),
        ('Multiple Selection', 'Multiple Selection'),
        ('Text', 'Text'),
    )
    sno = models.IntegerField(default=1)
    quiz = models.ForeignKey(Quiz, related_name="quiz_questions", on_delete=models.CASCADE)
    question = RichTextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES, default='Single Selection')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.question}"

    class Meta:
        verbose_name = '1.2 QuizQuestion'
        verbose_name_plural = '1.2 QuizQuestions'

class QuizQuestionOption(TimeStampModel):
    question = models.ForeignKey(QuizQuestion, related_name="question_options", on_delete=models.CASCADE)
    option = models.CharField(max_length=250)
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = '1.3 QuizQuestionOption'
        verbose_name_plural = '1.3 QuizQuestionOptions'

    def __str__(self):
        return f"{self.question} - {self.option}"

class QuizStudentMapper(TimeStampModel):
    student = models.ForeignKey(Person, related_name="student_mapper", on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    score = models.FloatField(default=0)

    class Meta:
        verbose_name = '1.4 QuizStudentMapper'
        verbose_name_plural = '1.4 QuizStudentMappers'


class QuizStudentAnswer(TimeStampModel):
    stu_mapper = models.ForeignKey(QuizStudentMapper, related_name='quiz_student_mapper_answers', on_delete=models.CASCADE)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    answer = models.CharField(max_length=250)
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = '1.4 QuizStudentAnswer'
        verbose_name_plural = '1.4 QuizStudentAnswers'