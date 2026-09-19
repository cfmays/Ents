import io
import shutil
import tempfile

from PIL import Image

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Enrichment

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='ents_test_media_')


def make_image_file(name='test.png', size=(100, 100), format='PNG'):
    buf = io.BytesIO()
    Image.new('RGB', size).save(buf, format=format)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


def tearDownModule():
    shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class EnrichmentModelTests(TestCase):

    def test_str_returns_name(self):
        e = Enrichment.objects.create(name='Ball', photo=make_image_file())
        self.assertEqual(str(e), 'Ball')

    def test_photo_file_name_returns_basename(self):
        e = Enrichment.objects.create(name='Ball', photo=make_image_file(name='toy.png'))
        self.assertTrue(e.photo_file_name().endswith('.png'))
        self.assertNotIn('/', e.photo_file_name())

    def test_name_must_be_unique(self):
        Enrichment.objects.create(name='Ball', photo=make_image_file())
        with self.assertRaises(Exception):
            Enrichment.objects.create(name='Ball', photo=make_image_file())

    def test_ordering_is_by_name(self):
        Enrichment.objects.create(name='Zebra', photo=make_image_file(name='z.png'))
        Enrichment.objects.create(name='Apple', photo=make_image_file(name='a.png'))
        names = list(Enrichment.objects.values_list('name', flat=True))
        self.assertEqual(names, ['Apple', 'Zebra'])

    def test_large_photo_is_resized_on_save(self):
        e = Enrichment.objects.create(
            name='Big', photo=make_image_file(name='big.png', size=(2000, 1000))
        )
        img = Image.open(e.photo.path)
        self.assertLessEqual(img.width, 540)
        self.assertLessEqual(img.height, 960)

    def test_small_photo_is_not_resized_on_save(self):
        e = Enrichment.objects.create(
            name='Small', photo=make_image_file(name='small.png', size=(100, 100))
        )
        img = Image.open(e.photo.path)
        self.assertEqual(img.size, (100, 100))

    def test_can_create_without_a_photo(self):
        # master-list items get preloaded by name/category before anyone has
        # uploaded a real photo for them; saving must not crash.
        e = Enrichment.objects.create(name='No Photo Yet')
        self.assertFalse(e.photo)


class IndexViewTests(TestCase):

    def test_index_loads_without_login(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class EnrichmentUploadViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        self.user.groups.add(supervisor_group)
        self.url = reverse('createView')

    def test_get_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_get_forbidden_for_logged_in_non_supervisor(self):
        User.objects.create_user(username='bob', password='password123')
        self.client.login(username='bob', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_allowed_for_superuser_without_supervisor_group(self):
        User.objects.create_superuser(username='root', email='root@example.com', password='password123')
        self.client.login(username='root', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_index_hides_new_item_link_for_non_supervisor(self):
        User.objects.create_user(username='carol', password='password123')
        self.client.login(username='carol', password='password123')
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'New Item')

    def test_index_shows_new_item_link_for_supervisor(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'New Item')
        self.assertNotContains(self.client.get(reverse('zoo:asg_list')), 'New Item')  # no longer in the menu bar

    def test_index_shows_new_item_link_for_superuser(self):
        User.objects.create_superuser(username='root2', email='root2@example.com', password='password123')
        self.client.login(username='root2', password='password123')
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'New Item')

    def test_get_renders_form_when_logged_in(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'createEnrichment.html')

    def test_post_valid_form_creates_enrichment_and_redirects(self):
        self.client.login(username='alice', password='password123')
        response = self.client.post(self.url, {
            'name': 'Kong Toy',
            'photo': make_image_file(),
        })
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(Enrichment.objects.filter(name='Kong Toy').exists())

    def test_post_invalid_form_reshows_form_with_errors(self):
        self.client.login(username='alice', password='password123')
        response = self.client.post(self.url, {'name': '', 'photo': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'createEnrichment.html')
        self.assertFalse(Enrichment.objects.exists())

    def test_post_requires_login(self):
        response = self.client.post(self.url, {
            'name': 'Kong Toy',
            'photo': make_image_file(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Enrichment.objects.exists())


class LogoutViewTests(TestCase):

    def test_logout_redirects_to_index(self):
        User.objects.create_user(username='alice', password='password123')
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('index'))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AjaxLoadSearchstringItemsTests(TestCase):

    def setUp(self):
        Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        Enrichment.objects.create(name='Rope', photo=make_image_file(name='rope.png'))

    def test_returns_all_items_when_not_searching(self):
        response = self.client.get(reverse('ajax_load_searchstring_items'), {
            'theSearchString': '',
            'theDoSearch': 'false',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ball')
        self.assertContains(response, 'Rope')

    def test_filters_items_by_search_string(self):
        response = self.client.get(reverse('ajax_load_searchstring_items'), {
            'theSearchString': 'Ba',
            'theDoSearch': 'true',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ball')
        self.assertNotContains(response, 'Rope')

    def test_up_to_three_search_strings_must_all_match_and_count_is_shown(self):
        Enrichment.objects.create(name='Ball- 12in Tiger', photo=make_image_file(name='b12.png'))
        Enrichment.objects.create(name='Ball- 6in Tiger', photo=make_image_file(name='b6.png'))
        Enrichment.objects.create(name='Ball- 12in Wolf', photo=make_image_file(name='w12.png'))
        response = self.client.get(reverse('ajax_load_searchstring_items'), {
            'theSearchString': 'ball',
            'theSearchString2': '12',
            'theSearchString3': ' tiger ',
            'theDoSearch': 'true',
        })
        self.assertContains(response, 'Ball- 12in Tiger')
        self.assertNotContains(response, 'Ball- 6in Tiger')
        self.assertNotContains(response, 'Ball- 12in Wolf')
        self.assertContains(response, 'data-count-text="1 item"')

        response = self.client.get(reverse('ajax_load_searchstring_items'), {'theSearchString': 'ball', 'theDoSearch': 'false'})
        self.assertContains(response, 'data-count-text="5 items"')  # search off: everything

    def test_index_header_shows_item_count(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Select Item (2 items)')
        self.assertContains(response, 'Enter search text')
        self.assertContains(response, 'id_searchString3')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AjaxGetImageUrlTests(TestCase):

    def test_returns_empty_url_when_no_item_given(self):
        response = self.client.get(reverse('ajax_get_image_url'))
        self.assertEqual(response.json(), {'theURL': ''})

    def test_returns_empty_url_when_item_not_found(self):
        response = self.client.get(reverse('ajax_get_image_url'), {'theItem': 999999})
        self.assertEqual(response.json(), {'theURL': ''})

    def test_returns_photo_url_for_existing_item(self):
        e = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        response = self.client.get(reverse('ajax_get_image_url'), {'theItem': e.id})
        data = response.json()
        self.assertIn('/media/', data['theURL'])
        self.assertIn('ball', data['theURL'])


class CaseInsensitiveLoginTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('maranda', password='1957')

    def test_login_succeeds_with_different_case_username(self):
        self.assertTrue(self.client.login(username='Maranda', password='1957'))

    def test_login_succeeds_with_original_case_username(self):
        self.assertTrue(self.client.login(username='maranda', password='1957'))

    def test_login_fails_with_wrong_password(self):
        self.assertFalse(self.client.login(username='MARANDA', password='wrong'))
