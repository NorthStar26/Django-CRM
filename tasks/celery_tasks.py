from celery import Celery
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import reverse
from django.template.loader import render_to_string

from accounts.models import Account, Email
from common.models import User
from contacts.models import Contact
from tasks.models import Task

app = Celery("crm", broker=settings.CELERY_BROKER_URL)


@app.task
def send_email(task_id, recipients, domain="demo.django-crm.io", protocol="http"):
    task = Task.objects.filter(id=task_id).first()
    created_by = task.created_by
    for user in recipients:
        recipients_list = []
        user = User.objects.filter(id=user, is_active=True).first()
        if user:
            recipients_list.append(user.email)
            subject = " Assigned a task for you ."
            context = {}
            context["task_title"] = task.title
            context["task_id"] = task.id
            context["task_created_by"] = task.created_by
            context["url"] = protocol + "://" + domain
            context["user"] = user
            html_content = render_to_string(
                "tasks_email_template.html", context=context
            )
            msg = EmailMessage(subject=subject, body=html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()

    # if task:
    #     subject = ' Assigned a task for you .'
    #     context = {}
    #     context['task_title'] = task.title
    #     context['task_id'] = task.id
    #     context['task_created_by'] = task.created_by
    #     context["url"] = protocol + '://' + domain + \
    #             reverse('tasks:task_detail', args=(task.id,))
    #     recipients = task.assigned_to.filter(is_active=True)
    #     if recipients.count() > 0:
    #         for recipient in recipients:
    #             context['user'] = recipient.email
    #             html_content = render_to_string(
    #                 'tasks_email_template.html', context=context)
    #             msg = EmailMessage(
    #                 subject=subject, body=html_content, to=[recipient.email, ])
    #             msg.content_subtype = "html"
    #             msg.send()
