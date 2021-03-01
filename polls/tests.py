import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from django.contrib.auth.models import User
from django.test.client import Client

from .models import Question


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """ 
        was_published_recently() returns False for questions whose
        pub_date is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)

        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)

        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the given number of `days` offset
    to now (negative for questions published in the past, positive for questions that have yet to be 
    published).
    """
    time = timezone.now() + datetime.timedelta(days=days)

    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question_with_choice(self):
        """
        Questions with a pub_date in the past and choices are displayed on the index page.
        """
        q = create_question(question_text="Past question.", days=-30)

        q.choice_set.create(choice_text='Choice for Past question.', votes=0) 

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], 
            ['<Question: Past question.>']
        )

    def test_future_question_with_choice(self):
        """
        Questions with a pub_date in the future and choices aren't displayed on the index page.
        """

        q = create_question(question_text="Future question.", days=30)

        q.choice_set.create(choice_text='Choice for Future question.', votes=0)

        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question_with_choice(self):
        """
        Even if both past and future questions exist with choices, only past questions are displayed.
        """
        q1 = create_question(question_text="Past question.", days=-30)
        q2 = create_question(question_text="Future question.", days=30)

        q1.choice_set.create(choice_text='Choice for Past question.', votes=0)
        q2.choice_set.create(choice_text='Choice for Future question.', votes=0)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions_with_choice(self):
        """
        The questions index page may display multiple questions that have choices.
        """
        q1 = create_question(question_text="Past question 1.", days=-30)
        q2 = create_question(question_text="Past question 2.", days=-5)

        q1.choice_set.create(choice_text='Choice for Past question 1.', votes=0)
        q2.choice_set.create(choice_text='Choice for Past question 2.', votes=0)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )
    
    def test_past_question_without_choice(self):
        """
        Questions without choices should not be published.
        """
        create_question(question_text="Question without choices", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future returns 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class QuestionResultsViewTests(TestCase):
    def test_future_question(self):
        """
        The results view of a question with a pub_date in the future returns 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:results', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The results view of a question with a pub_date in the past displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class AdminTests(TestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(username='admin', password='adminpassword')
        self.superuser.save()
    

    def test_superuser_can_see_future_question_with_choice(self):
    """
    Future question should be displayed for logged in superusers.
    """

    q = create_question(question_text='Future question.', days=30)

    q.choice_set.create(choice_text="Choice for Future question.", votes=0)

    self.client.force_login(self.user)

    response = self.client.get(reverse('polls:index'))

    self.assertQuerysetEqual(
        response.context['latest_question_list'],
        ['<Question: Future question.>']
    )


    def test_superuser_can_see_past_question_without_choices(self):
        """
        A question without choices should be displayed for logged in superusers.
        """

        create_question(question_text='Past question.', days=-30)
        
        self.client.force_login(self.user)

        response = self.client.get(reverse('polls:index'))

        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )


class LoggedUserTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='user', password='userpassword')
        self.user.save()


    def test_logged_user_can_see_future_question_with_choice(self):
        """
        Future question should not be displayed for ordinary logged in users.
        """

        q = create_question(question_text='Future question.', days=30)

        q.choice_set.create(choice_text="Choice for Future question.", votes=0)

        self.client.force_login(self.user)

        response = self.client.get(reverse('polls:index'))

        self.assertQuerysetEqual(response.context['latest_question_list'], [])


    def test_logged_user_can_see_past_question_without_choices(self):
        """
        A question without choices should not be displayed for ordinary logged in users.
        """

        create_question(question_text="Past question.", days=-30)

        self.client.force_login(self.user)

        response = self.client.get(reverse('polls:index'))

        self.assertQuerysetEqual(response.context['latest_question_list'],[])


class AnonymousUserTests(TestCase):
    def test_ordinary_user_can_see_future_question_with_choice(self):
        """
        Future question should not be displayed for ordinary users.
        """

        q = create_question(question_text="Future question.", days=30)

        q.choice_set.create(choice_text="Choice for Future question.", votes=0)

        response = self.client.get(reverse('polls:index'))

        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_ordinary_user_can_see_past_question_without_choices(self):
            """
            A question without choices should not be displayed for ordinary users.
            """

            create_question(question_text="Past question.", days=-30)

            response = self.client.get(reverse('polls:index'))

            self.assertQuerysetEqual(response.context['latest_question_list'], [])
