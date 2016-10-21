# coding: utf-8
from unittest.mock import patch

from django.conf import settings
from django.core.cache import caches

from th_twitter.models import Twitter
from th_twitter.forms import TwitterProviderForm, TwitterConsumerForm
from th_twitter.my_twitter import ServiceTwitter
from django_th.tests.test_main import MainTest


from twython import Twython

cache = caches['th_twitter']


class TwitterTest(MainTest):

    """
        TwitterTest Model
    """

    def test_get_config_th(self):
        """
            does this settings exists ?
        """
        self.assertTrue(settings.TH_TWITTER)
        self.assertIn('consumer_key', settings.TH_TWITTER)
        self.assertIn('consumer_secret', settings.TH_TWITTER)

    def test_get_config_th_cache(self):
        self.assertIn('th_twitter', settings.CACHES)

    def test_get_services_list(self):
        th_service = ('th_twitter.my_twitter.ServiceTwitter',)
        for service in th_service:
            self.assertIn(service, settings.TH_SERVICES)

    def create_twitter(self, tag='twitter', screen='@jondoe'):
        trigger = self.create_triggerservice(consumer_name='ServiceTwitter')
        status = True
        return Twitter.objects.create(tag=tag,
                                      screen=screen,
                                      since_id=1,
                                      trigger=trigger,
                                      status=status)

    def test_twitter(self):
        t = self.create_twitter()
        self.assertTrue(isinstance(t, Twitter))
        self.assertEqual(t.show(), "My Twitter %s %s" % (t.screen, t.tag))
        self.assertEqual(t.__str__(), "{}".format(t.screen))

    """
        Form
    """
    # provider

    def test_valid_provider_form(self):
        t = self.create_twitter()
        data = {'screen': t.screen, 'tag': t.tag}
        form = TwitterProviderForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_provider_form(self):
        form = TwitterProviderForm(data={})
        self.assertFalse(form.is_valid())

    # consumer
    def test_valid_consumer_form(self):
        t = self.create_twitter()
        data = {'screen': t.screen, 'tag': t.tag}
        form = TwitterConsumerForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_consumer_form(self):
        form = TwitterConsumerForm(data={})
        self.assertFalse(form.is_valid())


class ServiceTwitterTest(TwitterTest):
    """
       ServiceTwitterTest
    """

    def setUp(self):
        super(ServiceTwitterTest, self).setUp()
        self.data = {'text': 'something #thatworks'}
        self.token = 'QWERTY123#TH#12345'
        self.trigger_id = 1
        self.service = ServiceTwitter(self.token)

    @patch.object(Twython, 'search')
    def test_read_data_tag(self, mock1):
        t = self.create_twitter(tag='twitter', screen='')
        search = {'count': 100,
                  'q': 'twitter',
                  'result_type': 'recent',
                  'since_id': 1}
        kwargs = dict({'date_triggered': '2013-05-11 13:23:58+00:00',
                       'model_name': 'Twitter',
                       'trigger_id': t.trigger_id})

        se = ServiceTwitter(self.token)
        se.read_data(**kwargs)
        mock1.assert_called_with(**search)

    @patch.object(Twython, 'get_user_timeline')
    def test_read_data_screen(self, mock1):
        search = {'count': 200, 'screen_name': 'johndoe', 'since_id': 1}
        t = self.create_twitter(tag='', screen='johndoe')
        kwargs = dict({'date_triggered': '2013-05-11 13:23:58+00:00',
                       'model_name': 'Twitter',
                       'trigger_id': t.trigger_id})

        se = ServiceTwitter(self.token)
        se.read_data(**kwargs)
        mock1.assert_called_with(**search)

    @patch.object(Twython, 'update_status')
    def test_save_data(self, mock1):
        self.create_twitter()
        token = self.token
        trigger_id = self.trigger_id
        content = 'foobar #tag'
        self.data['title'] = 'a title'
        self.data['link'] = 'http://domain.ltd'

        self.assertTrue(token)
        self.assertTrue(isinstance(trigger_id, int))
        self.assertIn('text', self.data)
        self.assertNotEqual(self.data['text'], '')

        se = ServiceTwitter(self.token)
        se.save_data(trigger_id, **self.data)
        mock1.assert_called_once(status=content)
