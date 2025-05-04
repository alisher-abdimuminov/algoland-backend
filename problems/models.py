from uuid import uuid4
from django.db import models

from users.models import User


PROBLEM_DIFFICULTY = (
    ("easy", "Oson"),
    ("medium", "O'rtacha"),
    ("hard", "Qiyin"),
)


def upload_to_tests(instance: "Problem", filename):
    return f"files/problems/{instance.uuid}/tests.zip"


class Tag(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    uuid = models.CharField(max_length=100, default=uuid4)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Language(models.Model):
    uuid = models.CharField(max_length=100, default=uuid4)
    name = models.CharField(max_length=100)
    short = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=(("compiled", "Compiled",), ("interpreted", "Interpreted", )))
    file = models.CharField(max_length=100)
    sandbox = models.CharField(max_length=100, default="sandbox")
    compile = models.CharField(max_length=100, null=True, blank=True)
    run = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    def parse_command(self, type: str = "compile", **kwargs):
        if type == "compile":
            command = self.compile
            for kwarg in kwargs:
                command = command.replace(kwarg, kwargs[kwarg])
            return command
        else:
            command = self.run
            for kwarg in kwargs:
                command = command.replace(kwarg, kwargs[kwarg])
            return command
    

class Problem(models.Model):
    uuid = models.CharField(max_length=100, default=uuid4)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    title = models.CharField(max_length=100)
    description = models.JSONField(default=dict, null=True, blank=True)
    hint = models.JSONField(default=dict, null=True, blank=True)
    input = models.JSONField(default=dict, null=True, blank=True)
    output = models.JSONField(default=dict, null=True, blank=True)
    samples = models.JSONField(default=list, null=True, blank=True)
    rank = models.IntegerField(default=800)
    difficulty = models.CharField(max_length=100, choices=PROBLEM_DIFFICULTY)

    time_limit = models.IntegerField(default=1)
    memory_limit = models.IntegerField(default=64)
    code_limit = models.IntegerField(default=10000)
    output_limit = models.IntegerField(default=1000)
    line_limit = models.IntegerField(default=1000)

    language = models.CharField(max_length=10)
    tags = models.ManyToManyField(Tag, related_name="problem_tags", blank=True)
    languages = models.ManyToManyField(Language, related_name="problem_allowed_languages", blank=True)
    tests = models.FileField(upload_to=upload_to_tests, null=True, blank=True)

    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    with_link = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Attempt(models.Model):
    uuid = models.CharField(max_length=100, default=uuid4)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, default="running", null=True, blank=True)
    code = models.TextField(null=True, blank=True)
    time = models.FloatField(default=0, null=True, blank=True)
    memory = models.IntegerField(default=0, null=True, blank=True)
    length = models.IntegerField(default=0, null=True, blank=True)
    cases = models.JSONField(default=list, null=True, blank=True)
    test = models.IntegerField(default=0)
    error = models.TextField(null=True, blank=True)
    output = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.uuid)
    

class Top(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="top_attempt_author")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="top_attempt_problem")
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="top_attempt_self")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.author.username
