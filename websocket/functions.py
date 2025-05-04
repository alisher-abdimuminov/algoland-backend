from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from sandbox import Judge
from users.models import (
    User,
    Notification,    
)
from users.serializers import (
    ProfileSerializer,
)
from posts.models import Post
from datetime import datetime
from users.models import Activity
from problems.models import (
    Problem,
    Attempt,
    Language,
    Top,
)
from posts.serializers import (
    PostModelSerializer,
)


# change user last_seen
def save_user_last_seen(user: User, last_seen: str):
    user.last_seen = last_seen
    user.save()


# change notifications is_readed field
def read_notifications(user: User):
    notifications = Notification.objects.filter(to=user, is_readed=False).exclude(type="all").update(is_readed=True)


# create and check attempt with given problem_uuid, language_uuid and code
def run_sandbox(user: User, problem_uuid: str, language_uuid: str, code: str):
    today = datetime.today()
    activity = Activity.objects.filter(author=user, created=today.date())

    if not activity.exists():
        activity = Activity.objects.create(author=user)
    else:
        activity = activity.first()
    problem = Problem.objects.filter(uuid=problem_uuid)
    language = Language.objects.filter(uuid=language_uuid)

    print(user, problem, language)

    if user.is_authenticated and problem.exists() and language.exists():
        problem = problem.first()
        language = language.first()
        top = Top.objects.filter(author=user, problem=problem)

        attempt = Attempt.objects.create(author=user, problem=problem, language=language, code=code)

        # run code with sandbox
        sandbox = Judge(attempt=attempt)
        sandbox.run()

        # change top attempt (with time)
        if not top.exists():
            top = Top.objects.create(author=user, problem=problem, attempt=attempt)
        else:
            top = top.first()
            if attempt.status == "ac" and attempt.time < top.attempt.time:
                top.attempt = attempt
                top.save()
        
        # change activity
        activity.attempts += 1
        activity.save()
        print("Runned")


# when user likes to the post
def like_post(user: User, post_uuid: str):
    post = Post.objects.filter(uuid=post_uuid)
    channel_layer = get_channel_layer()

    if post.exists():
        post = post.first()
        post.likes.add(user)
        post.save()
        Notification.objects.create(
            type="like_to_post",
            to=post.author,
            title="Like to post",
            content="Ali likes to your post",
            props={
                "user": {
                    "uuid": str(user.uuid),
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_premium": user.is_premium,
                },
                "post": {
                    "uuid": str(post.uuid),
                    "title": post.title,
                }
            }
        )

        async_to_sync(channel_layer.group_send)(
            "main",
            {
                "type": "update_post",
                "data": {
                    "post": PostModelSerializer(post, context={ "user": user }).data,
                },
            }
        )


def follow(user: User, username: str):
    target = User.objects.filter(username=username)

    print(user, target)
    if target.exists():
        target = target.first()

        target.followers.add(user)
        target.save()

        user.following.add(target)
        user.save()

        Notification.objects.create(
            type="follow",
            to=target,
            title="New follower",
            content=f"{user.username} follows you",
            props={
                "user": {
                    "uuid": str(user.uuid),
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_premium": user.is_premium,
                }
            }
        )

def unfollow(user: User, username: str):
    target = User.objects.filter(username=username)

    if target.exists():
        target = target.first()

        target.followers.remove(user)
        target.save()

        user.following.remove(target)
        user.save()

        Notification.objects.create(
            type="unfollow",
            to=target,
            title="Follower exited",
            content=f"{user.username} unfollow you",
            props={
                "user": {
                    "uuid": str(user.uuid),
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_premium": user.is_premium,
                }
            }
        )

