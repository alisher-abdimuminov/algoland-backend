from rest_framework import serializers
from django.db.models import Count, Q

from users.serializers import ProfileSerializer

from .models import (
    Problem,
    Language,
    Attempt,
    Tag,
    Top,
)


class TagModelSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    class Meta:
        model = Tag
        fields = ("id", "uuid", "name",)


class LanguageModelSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    class Meta:
        model = Language
        fields = ("id", "uuid", "name", "short", "icon", )


class ProblemsModelSerializer(serializers.ModelSerializer):
    author = ProfileSerializer()
    tags = TagModelSerializer(many=True)
    order = serializers.IntegerField(read_only=True)
    status = serializers.SerializerMethodField("status_func")
    acceptance = serializers.SerializerMethodField("acceptance_func")

    def status_func(self, obj: Problem):
        request = self.context.get("request")

        if not request:
            return "not_attempted"
        
        user = request.user

        if not user:
            return "not_attempted"
        
        if not user.is_authenticated:
            return "not_attempted"
        
        attempts = Attempt.objects.filter(author=user, problem=obj)

        if not attempts.exists():
            return "not_attempted"
        else:
            if not attempts.filter(status="ac").exists():
                return "attempted"
            else:
                return "solved"

    def acceptance_func(self, obj: Problem):
        attempts = Attempt.objects.filter(problem=obj).aggregate(
            total=Count('id'),
            accepted=Count('id', filter=Q(status='ac'))
        )
        total = attempts.get('total', 0)
        accepted = attempts.get('accepted', 0)

        if total == 0:
            return 0
        return round((accepted / total) * 100, 1)


    class Meta:
        model = Problem
        fields = ("order", "uuid", "title", "author", "status", "acceptance", "tags", "rank", "difficulty", "time_limit", "memory_limit", "is_public", )
        read_only_fields = ("order",)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        author_data = ProfileSerializer(instance.author, context=self.context).data
        data['author'] = author_data
        return data


class ProblemModelSerializer(serializers.ModelSerializer):
    author = ProfileSerializer()
    tags = TagModelSerializer(many=True)
    languages = LanguageModelSerializer(many=True)
    order = serializers.IntegerField(read_only=True)
    status = serializers.SerializerMethodField("status_func")
    acceptance = serializers.SerializerMethodField("acceptance_func")

    def status_func(self, obj: Problem):
        request = self.context.get("request")

        if not request:
            return "not_attempted"
        
        user = request.user

        if not user:
            return "not_attempted"
        
        if not user.is_authenticated:
            return "not_attempted"

        top = Top.objects.filter(author=user, problem=obj)

        if not top.exists():
            return "not_attempted"
        else:
            if not top.filter(attempt__status="ac").exists():
                return "attempted"
            else:
                return "solved"
            
    def acceptance_func(self, obj: Problem):
        attempts = Attempt.objects.filter(problem=obj).aggregate(
            total=Count('id'),
            accepted=Count('id', filter=Q(status='ac'))
        )
        total = attempts.get('total', 0)
        accepted = attempts.get('accepted', 0)

        if total == 0:
            return 0
        return round((accepted / total) * 100, 1)
    
    class Meta:
        model = Problem
        fields = ("order", "uuid", "title", "author", "status", "acceptance", "tags", "description", "hint", "input", "output", "samples", "rank", "difficulty", "time_limit", "memory_limit", "language", "languages", "with_link", "is_public", )
        read_only_fields = ("order",)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        author_data = ProfileSerializer(instance.author, context=self.context).data
        data['author'] = author_data
        return data


class EditProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ("title", "description", "hint", "input", "output", "samples", "difficulty", "time_limit", "memory_limit", "language", "languages", "tags", "with_link", )


class AttemptsModelSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    language = LanguageModelSerializer()
    class Meta:
        model = Attempt
        fields = ("id", "uuid", "status", "language", "code", "time", "memory", "error", "test", "cases", "created", )
