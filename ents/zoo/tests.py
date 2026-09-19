import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse

from ents.models import Enrichment
from ents.tests import make_image_file

from .models import SpecialConcern, ASG, ASGApprovedItem, Animal, Behavior, BehaviorGoal, BehaviorScore, CalendarEntry, Division, Reinforcer, String, TrainingAnimal

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='zoo_test_media_')


def tearDownModule():
    shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ASGApprovedItemTests(TestCase):

    def test_food_and_non_food_items_are_split_by_assignment_flag(self):
        string = String.objects.create(name='Test String')
        asg = ASG.objects.create(name='Test ASG', string=string)
        food_item = Enrichment.objects.create(name='Grapes', photo=make_image_file(name='grapes.png'))
        toy_item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        ASGApprovedItem.objects.create(asg=asg, item=food_item, is_food=True)
        ASGApprovedItem.objects.create(asg=asg, item=toy_item)

        assignments = ASGApprovedItem.objects.filter(asg=asg).select_related('item')
        self.assertEqual(list(assignments.filter(is_food=True).values_list('item__name', flat=True)), ['Grapes'])
        self.assertEqual(list(assignments.filter(is_food=False).values_list('item__name', flat=True)), ['Ball'])


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class CalendarEntryTests(TestCase):

    def test_only_date_and_item_are_required(self):
        string = String.objects.create(name='Test String')
        asg = ASG.objects.create(name='Test ASG', string=string)
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        entry = CalendarEntry.objects.create(asg=asg, date='2026-09-02', item=item)
        entry.full_clean(exclude=['animal', 'behavior_goal'])  # only optional fields left blank
        self.assertIsNone(entry.behavior_goal)
        self.assertEqual(entry.gbs_score, '')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TrainingFlowTests(TestCase):

    def setUp(self):
        self.string = String.objects.create(name='Fossa String')
        self.animal = TrainingAnimal.objects.create(name='Mee-Noi', string=self.string)
        self.maintenance_behavior = Behavior.objects.create(name='Target', behavior_type='maintenance')
        self.new_behavior = Behavior.objects.create(name='Crate', behavior_type='new')
        self.animal.maintenance_behaviors.add(self.maintenance_behavior)
        self.animal.new_behaviors.add(self.new_behavior)
        self.reinforcer = Reinforcer.objects.create(name='Grapes')
        self.animal.reinforcers.add(self.reinforcer)

        self.keeper = User.objects.create_user('keeper', password='pw')
        self.keeper.strings.add(self.string)

    def test_training_entry_form_shows_only_this_animals_behaviors(self):
        self.client.force_login(self.keeper)
        response = self.client.get(reverse('zoo:training_entry', args=[self.animal.id]))
        self.assertContains(response, 'Target')
        self.assertContains(response, 'Crate')

    def test_submitting_training_session_creates_behavior_scores(self):
        self.client.force_login(self.keeper)
        response = self.client.post(reverse('zoo:training_entry', args=[self.animal.id]), {
            'date': '2026-09-15',
            'reinforcer_1': self.reinforcer.id,
            f'behavior_{self.maintenance_behavior.id}': '4',
            f'behavior_{self.new_behavior.id}': '3',
        })
        self.assertEqual(response.status_code, 302)
        session = self.animal.training_sessions.get()
        self.assertEqual(session.trainer, self.keeper)
        self.assertEqual(session.reinforcer_1, self.reinforcer)
        self.assertIsNone(session.reinforcer_2)
        scores = {score.behavior_id: score.score for score in session.behavior_scores.all()}
        self.assertEqual(scores[self.maintenance_behavior.id], 4)
        self.assertEqual(scores[self.new_behavior.id], 3)

        self.keeper.profile.refresh_from_db()
        self.assertEqual(self.keeper.profile.last_training_string, self.string)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class KeeperAccessScopingTests(TestCase):

    def setUp(self):
        self.division = Division.objects.create(name='Aquatic')
        self.string = String.objects.create(name='Aquarium Bird/ Reptile', division=self.division)
        self.asg = ASG.objects.create(name='Penguin', string=self.string)
        self.animal = TrainingAnimal.objects.create(name='Penguin-African, Carl', string=self.string)

        self.assigned_keeper = User.objects.create_user('sarahh', password='1957')
        self.assigned_keeper.strings.add(self.string)

        self.unassigned_keeper = User.objects.create_user('audrey', password='1957')

        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        self.matching_supervisor = User.objects.create_user('boss2', password='pw', is_staff=True)
        self.matching_supervisor.groups.add(supervisor_group)
        self.matching_supervisor.profile.divisions.add(self.division)

        self.superuser = User.objects.create_superuser('root2', 'root2@example.com', 'pw')

    def test_unassigned_keeper_cannot_open_calendar(self):
        self.client.force_login(self.unassigned_keeper)
        response = self.client.get(reverse('zoo:calendar_tab', args=[self.asg.id]))
        self.assertEqual(response.status_code, 403)

    def test_unassigned_keeper_cannot_open_list_management_or_reporting_or_training(self):
        self.client.force_login(self.unassigned_keeper)
        self.assertEqual(self.client.get(reverse('zoo:list_management_tab', args=[self.asg.id])).status_code, 403)
        self.assertEqual(self.client.get(reverse('zoo:reporting_view', args=[self.asg.id])).status_code, 403)
        self.assertEqual(self.client.get(reverse('zoo:training_entry', args=[self.animal.id])).status_code, 403)

    def test_assigned_keeper_can_open_calendar(self):
        self.client.force_login(self.assigned_keeper)
        response = self.client.get(reverse('zoo:calendar_tab', args=[self.asg.id]))
        self.assertEqual(response.status_code, 200)

    def test_asg_list_only_shows_accessible_strings(self):
        self.client.force_login(self.unassigned_keeper)
        response = self.client.get(reverse('zoo:asg_list'))
        self.assertNotContains(response, 'Penguin')

        self.client.force_login(self.assigned_keeper)
        response = self.client.get(reverse('zoo:asg_list'))
        self.assertContains(response, 'Penguin')

    def test_supervisor_in_matching_division_can_open_calendar(self):
        self.client.force_login(self.matching_supervisor)
        response = self.client.get(reverse('zoo:calendar_tab', args=[self.asg.id]))
        self.assertEqual(response.status_code, 200)

    def test_superuser_can_open_calendar(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('zoo:calendar_tab', args=[self.asg.id]))
        self.assertEqual(response.status_code, 200)

    def test_calendar_animal_dropdown_offers_the_calendars_choices_only(self):
        Animal.objects.create(asg=self.asg, name='Carl/ Pat')
        other = ASG.objects.create(name='Other', string=self.string)
        Animal.objects.create(asg=other, name='Someone Else')
        self.client.force_login(self.assigned_keeper)
        response = self.client.get(reverse('zoo:calendar_tab', args=[self.asg.id]))
        self.assertContains(response, 'Carl/ Pat')
        self.assertNotContains(response, 'Someone Else')

    def test_calendar_item_dropdown_shows_name_and_comments(self):
        item = Enrichment.objects.create(name='Ball- 24”', photo=make_image_file(name='b24.png'))
        plain = Enrichment.objects.create(name='Feathers', photo=make_image_file(name='f.png'))
        ASGApprovedItem.objects.create(asg=self.asg, item=item, comments='Stays up at tiger')
        ASGApprovedItem.objects.create(asg=self.asg, item=item, is_food=True, comments='Frozen')
        ASGApprovedItem.objects.create(asg=self.asg, item=plain)
        self.client.force_login(self.assigned_keeper)
        response = self.client.get(reverse('zoo:calendar_tab', args=[self.asg.id]))
        self.assertContains(response, 'Ball- 24” **Stays up at tiger | Frozen')
        self.assertContains(response, '>Feathers</option>')

    def test_calendar_row_with_note_but_no_date_shows_message(self):
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        ASGApprovedItem.objects.create(asg=self.asg, item=item)
        self.client.force_login(self.assigned_keeper)
        data = {
            'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0', 'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
            'form-0-date': '', 'form-0-item': str(item.id), 'form-0-notes': 'chewed it',
        }
        response = self.client.post(reverse('zoo:calendar_tab', args=[self.asg.id]), data)
        self.assertContains(response, 'Please enter a date.')
        self.assertFalse(CalendarEntry.objects.exists())

        data['form-0-item'] = ''
        data['form-0-date'] = '2026-09-02'
        response = self.client.post(reverse('zoo:calendar_tab', args=[self.asg.id]), data)
        self.assertContains(response, 'Please choose an enrichment item.')

    def test_calendar_page_is_not_cached_by_the_browser(self):
        self.client.force_login(self.assigned_keeper)
        response = self.client.get(reverse('zoo:calendar_tab', args=[self.asg.id]))
        self.assertIn('no-store', response['Cache-Control'])

    def test_print_view_has_entries_but_not_score_or_note_columns(self):
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        ASGApprovedItem.objects.create(asg=self.asg, item=item, comments='Stays up')
        CalendarEntry.objects.create(asg=self.asg, date='2026-09-03', item=item, do_score=3, notes='secret keeper note')
        url = reverse('zoo:calendar_print', args=[self.asg.id, 2026, 9])

        self.client.force_login(self.assigned_keeper)
        response = self.client.get(url)
        self.assertContains(response, 'Ball **Stays up')
        self.assertContains(response, 'Enrichment item')
        for hidden in ('>DO<', '>IO<', '>GBS<', '>Notes<', 'secret keeper note'):
            self.assertNotContains(response, hidden)

        self.client.force_login(self.unassigned_keeper)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_save_and_print_goes_to_the_print_page_only_when_saved(self):
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        ASGApprovedItem.objects.create(asg=self.asg, item=item)
        self.client.force_login(self.assigned_keeper)
        url = reverse('zoo:calendar_tab', args=[self.asg.id, 2026, 9])
        data = {
            'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0', 'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
            'form-0-date': '2026-09-05', 'form-0-item': str(item.id), 'print_after': '1',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('zoo:calendar_print', args=[self.asg.id, 2026, 9]))
        self.assertEqual(CalendarEntry.objects.count(), 1)

        data['form-0-date'] = ''  # invalid row: stays on the calendar with the message, nothing extra saved
        self.assertContains(self.client.post(url, data), 'Please enter a date.')

    def test_saving_a_date_outside_the_month_shows_an_error(self):
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        ASGApprovedItem.objects.create(asg=self.asg, item=item)
        self.client.force_login(self.assigned_keeper)
        data = {
            'form-TOTAL_FORMS': '2', 'form-INITIAL_FORMS': '0', 'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
            'form-0-date': '2026-09-05', 'form-0-item': str(item.id),
            'form-1-date': '2026-10-05', 'form-1-item': str(item.id),
        }
        response = self.client.post(reverse('zoo:calendar_tab', args=[self.asg.id, 2026, 9]), data)
        self.assertContains(response, 'Date must be in September 2026.')
        self.assertNotContains(response, 'Please enter a date.')
        self.assertFalse(CalendarEntry.objects.exists())  # nothing saved until the row is fixed

    def test_copy_and_paste_month_drops_days_that_do_not_exist(self):
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        gone = Enrichment.objects.create(name='Rope', photo=make_image_file(name='rope.png'))
        ASGApprovedItem.objects.create(asg=self.asg, item=item)
        ASGApprovedItem.objects.create(asg=self.asg, item=gone)
        choice = Animal.objects.create(asg=self.asg, name='Carl')
        goal = BehaviorGoal.objects.create(name='Roll')
        self.asg.behavior_goals.add(goal)
        CalendarEntry.objects.create(asg=self.asg, date='2026-08-03', item=item, animal=choice, behavior_goal=goal, do_score=3, notes='x')
        CalendarEntry.objects.create(asg=self.asg, date='2026-08-31', item=item)
        CalendarEntry.objects.create(asg=self.asg, date='2026-08-10', item=gone)
        ASGApprovedItem.objects.filter(asg=self.asg, item=gone).delete()

        self.client.force_login(self.assigned_keeper)
        self.client.post(reverse('zoo:calendar_copy', args=[self.asg.id, 2026, 8]))  # no form data: copies saved entries
        response = self.client.post(reverse('zoo:calendar_paste', args=[self.asg.id, 2026, 9]), follow=True)

        september = CalendarEntry.objects.filter(date__year=2026, date__month=9)
        self.assertEqual(september.count(), 1)
        entry = september.get()
        self.assertEqual((entry.date.day, entry.animal, entry.behavior_goal), (3, choice, goal))
        self.assertIsNone(entry.do_score)  # scores and notes are not copied
        self.assertEqual(entry.notes, '')
        self.assertContains(response, 'has no day 31')
        self.assertContains(response, 'no longer approved')

        response = self.client.post(reverse('zoo:calendar_paste', args=[self.asg.id, 2026, 9]), follow=True)
        self.assertEqual(september.count(), 1)  # pasting twice doesn't duplicate
        self.assertContains(response, 'already in this month')

    def test_copy_uses_unsaved_rows_on_the_page(self):
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        ASGApprovedItem.objects.create(asg=self.asg, item=item)
        self.client.force_login(self.assigned_keeper)
        url = reverse('zoo:calendar_copy', args=[self.asg.id, 2026, 8])
        data = {
            'form-TOTAL_FORMS': '2', 'form-INITIAL_FORMS': '0', 'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
            'form-0-date': '2026-08-05', 'form-0-item': str(item.id),
            'form-1-date': '', 'form-1-item': '',
        }
        reply = self.client.post(url, data).json()
        self.assertEqual(reply['level'], 'success')
        self.assertEqual(self.client.session['calendar_clipboard']['entries'][0]['day'], 5)
        self.assertFalse(CalendarEntry.objects.exists())  # copying saves nothing

        data['form-1-notes'] = 'no date or item'
        reply = self.client.post(url, data).json()
        self.assertEqual(reply['level'], 'warning')
        self.assertIn('Please enter a date.', reply['message'])

    def test_paste_without_copy_or_from_another_calendar_is_refused(self):
        self.client.force_login(self.assigned_keeper)
        response = self.client.post(reverse('zoo:calendar_paste', args=[self.asg.id, 2026, 9]), follow=True)
        self.assertContains(response, 'Nothing to paste yet')

        other = ASG.objects.create(name='Other', string=self.string)
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))
        CalendarEntry.objects.create(asg=other, date='2026-08-03', item=item)
        self.client.post(reverse('zoo:calendar_copy', args=[other.id, 2026, 8]))
        response = self.client.post(reverse('zoo:calendar_paste', args=[self.asg.id, 2026, 9]), follow=True)
        self.assertContains(response, 'only works within the same calendar')
        self.assertFalse(CalendarEntry.objects.filter(asg=self.asg).exists())

    def test_supervisor_can_add_and_remove_concerns_and_goals_but_keeper_cannot(self):
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        supervisor = User.objects.create_user('boss3', password='pw', is_staff=True)
        supervisor.groups.add(supervisor_group)
        supervisor.profile.divisions.add(self.division)
        url = reverse('zoo:list_management_tab', args=[self.asg.id])

        self.client.force_login(supervisor)
        self.client.post(url, {'add_concern': '  No   steel in tires '})
        self.client.post(url, {'add_concern': 'no steel in tires'})  # same text: reuses the concern
        self.client.post(url, {'add_goal_text': 'Roll'})
        self.assertEqual(SpecialConcern.objects.count(), 1)
        concern = self.asg.special_concerns.get()
        goal = self.asg.behavior_goals.get()
        self.assertEqual((concern.text, goal.name), ('No steel in tires', 'Roll'))

        self.client.post(url, {'remove_concern': concern.id})
        self.client.post(url, {'remove_goal': goal.id})
        self.assertFalse(self.asg.special_concerns.exists() or self.asg.behavior_goals.exists())
        self.assertTrue(SpecialConcern.objects.filter(pk=concern.id).exists())  # only unlinked from this calendar

        self.client.force_login(self.assigned_keeper)
        self.assertEqual(self.client.post(url, {'add_concern': 'Sneaky'}).status_code, 403)
        self.assertEqual(self.client.post(url, {'remove_concern': concern.id}).status_code, 403)
        self.assertFalse(SpecialConcern.objects.filter(text='Sneaky').exists())
        self.assertNotContains(self.client.get(url), 'Add concern')

    def test_supervisor_can_add_and_remove_approved_items_but_keeper_cannot(self):
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        supervisor = User.objects.create_user('boss4', password='pw', is_staff=True)
        supervisor.groups.add(supervisor_group)
        supervisor.profile.divisions.add(self.division)
        item = Enrichment.objects.create(name='Coloring', photo=make_image_file(name='c.png'))
        url = reverse('zoo:list_management_tab', args=[self.asg.id])

        self.client.force_login(supervisor)
        self.client.post(url, {'add_item': 'nonfood', 'item': item.id, 'comments': 'Non-toxic only', 'rate': '2'})
        self.client.post(url, {'add_item': 'food', 'item': item.id})  # same item, other column
        self.client.post(url, {'add_item': 'food', 'item': item.id})  # duplicate: ignored
        rows = ASGApprovedItem.objects.filter(asg=self.asg)
        self.assertEqual(rows.count(), 2)
        nonfood = rows.get(is_food=False)
        self.assertEqual((nonfood.comments, nonfood.rate), ('Non-toxic only', '2'))
        response = self.client.get(url)
        self.assertContains(response, 'Approved non-food enrichment')
        self.assertContains(response, 'Approved food enrichment')
        self.assertContains(response, '1 item<')  # one item in each column

        self.client.post(url, {'remove_item': nonfood.id})
        self.assertEqual(rows.count(), 1)

        self.client.force_login(self.assigned_keeper)
        self.assertEqual(self.client.post(url, {'add_item': 'food', 'item': item.id, 'comments': 'x'}).status_code, 403)
        self.assertEqual(self.client.post(url, {'remove_item': rows.get().id}).status_code, 403)
        self.assertEqual(rows.count(), 1)
        self.assertNotContains(self.client.get(url), 'Add item')

    def test_keeper_can_add_and_remove_animal_choice(self):
        self.client.force_login(self.assigned_keeper)
        url = reverse('zoo:list_management_tab', args=[self.asg.id])
        self.client.post(url, {'name': 'Rocky/ Raza'})
        choice = self.asg.animals.get()
        self.assertEqual(choice.name, 'Rocky/ Raza')
        self.client.post(url, {'remove_animal': choice.id})
        self.assertFalse(self.asg.animals.exists())

    def test_training_animals_list_follows_string_access(self):
        self.client.force_login(self.assigned_keeper)
        url = reverse('zoo:training_ajax_animals_for_string')
        self.assertContains(self.client.get(url, {'string_id': self.string.id}), 'Penguin-African, Carl')
        self.client.force_login(self.unassigned_keeper)
        self.assertNotContains(self.client.get(url, {'string_id': self.string.id}), 'Penguin-African, Carl')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SupervisorPermissionTests(TestCase):

    def setUp(self):
        self.division = Division.objects.create(name='Terrestrial')
        self.keeper = User.objects.create_user('keeper2', password='pw')
        self.supervisor = User.objects.create_user('boss', password='pw')
        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        self.supervisor.groups.add(supervisor_group)
        self.supervisor.profile.divisions.add(self.division)

    def test_keeper_cannot_reach_item_assignment_view(self):
        self.client.force_login(self.keeper)
        response = self.client.get(reverse('zoo:item_assignment'))
        self.assertEqual(response.status_code, 403)

    def test_supervisor_can_reach_item_assignment_view(self):
        self.client.force_login(self.supervisor)
        response = self.client.get(reverse('zoo:item_assignment'))
        self.assertEqual(response.status_code, 200)

    def test_supervisor_bulk_assign_creates_asg_approved_items(self):
        string = String.objects.create(name='Test String', division=self.division)
        asg1 = ASG.objects.create(name='ASG One', string=string)
        asg2 = ASG.objects.create(name='ASG Two', string=string)
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))

        self.client.force_login(self.supervisor)
        response = self.client.post(reverse('zoo:item_assignment'), {
            'items': [item.id],
            'asgs': [asg1.id, asg2.id],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ASGApprovedItem.objects.filter(item=item).count(), 2)

    def test_supervisor_cannot_assign_items_to_other_divisions_asg(self):
        other_division = Division.objects.create(name='Aquatic')
        other_string = String.objects.create(name='Other String', division=other_division)
        other_asg = ASG.objects.create(name='Other ASG', string=other_string)
        item = Enrichment.objects.create(name='Ball', photo=make_image_file(name='ball.png'))

        self.client.force_login(self.supervisor)
        response = self.client.post(reverse('zoo:item_assignment'), {
            'items': [item.id],
            'asgs': [other_asg.id],
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered with a validation error
        self.assertEqual(ASGApprovedItem.objects.filter(item=item).count(), 0)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DivisionScopingTests(TestCase):

    def setUp(self):
        self.division_a = Division.objects.create(name='Terrestrial')
        self.division_b = Division.objects.create(name='Aquatic')
        self.string_a = String.objects.create(name='String A', division=self.division_a)
        self.string_b = String.objects.create(name='String B', division=self.division_b)
        self.asg_a = ASG.objects.create(name='ASG A', string=self.string_a)
        self.asg_b = ASG.objects.create(name='ASG B', string=self.string_b)

        supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
        self.supervisor_a = User.objects.create_user('supA', password='pw', is_staff=True)
        self.supervisor_a.groups.add(supervisor_group)
        self.supervisor_a.profile.divisions.add(self.division_a)

        self.superuser = User.objects.create_superuser('root', 'root@example.com', 'pw')

    def test_supervisor_changelist_only_shows_own_division(self):
        self.client.force_login(self.supervisor_a)
        response = self.client.get('/admin/zoo/asg/')
        self.assertContains(response, 'ASG A')
        self.assertNotContains(response, 'ASG B')

    def test_supervisor_cannot_open_other_divisions_object(self):
        self.client.force_login(self.supervisor_a)
        response = self.client.get(f'/admin/zoo/asg/{self.asg_b.id}/change/')
        self.assertEqual(response.status_code, 302)  # "does not exist" redirect, not the change form
        response = self.client.get(f'/admin/zoo/asg/{self.asg_a.id}/change/')
        self.assertEqual(response.status_code, 200)

    def test_supervisor_add_form_only_offers_own_division_strings(self):
        self.client.force_login(self.supervisor_a)
        response = self.client.get('/admin/zoo/asg/add/')
        self.assertContains(response, 'String A')
        self.assertNotContains(response, 'String B')

    def test_superuser_sees_both_divisions(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/admin/zoo/asg/')
        self.assertContains(response, 'ASG A')
        self.assertContains(response, 'ASG B')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ManageTrainingTests(TestCase):

    def setUp(self):
        self.division_a = Division.objects.create(name='Terrestrial')
        self.division_b = Division.objects.create(name='Aquatic')
        self.string_a = String.objects.create(name='String A', division=self.division_a)
        self.string_b = String.objects.create(name='String B', division=self.division_b)
        self.animal = TrainingAnimal.objects.create(name='Rocky', string=self.string_a)
        self.animal_b = TrainingAnimal.objects.create(name='Carl', string=self.string_b)

        group, _ = Group.objects.get_or_create(name='Supervisor')
        self.supervisor = User.objects.create_user('supa', password='pw', is_staff=True)
        self.supervisor.groups.add(group)
        self.supervisor.profile.divisions.add(self.division_a)
        self.superuser = User.objects.create_superuser('rootm', 'r@example.com', 'pw')
        self.keeper = User.objects.create_user('kate', password='pw')
        self.url = reverse('zoo:manage_training')

    def post(self, do, **data):
        return self.client.post(self.url, {'do': do, **data}, follow=True)

    def test_link_and_page_are_for_supervisors_only(self):
        start = reverse('zoo:training_start')
        self.client.force_login(self.keeper)
        self.assertNotContains(self.client.get(start), 'Manage training logs')
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_login(self.supervisor)
        self.assertContains(self.client.get(start), 'Manage training logs')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_supervisor_only_sees_and_changes_own_division(self):
        self.client.force_login(self.supervisor)
        page = self.client.get(self.url)
        self.assertContains(page, 'String A')
        self.assertNotContains(page, 'String B')
        self.assertEqual(self.client.post(self.url, {'do': f'add_animal:{self.string_b.id}', f'new_animal_{self.string_b.id}': 'X'}).status_code, 404)
        self.assertEqual(self.client.post(self.url, {'do': f'delete_animal:{self.animal_b.id}'}).status_code, 404)
        self.assertTrue(TrainingAnimal.objects.filter(pk=self.animal_b.pk).exists())

    def test_supervisor_without_division_is_told_why_the_page_is_empty(self):
        loner = User.objects.create_user('loner', password='pw', is_staff=True)
        loner.groups.add(Group.objects.get(name='Supervisor'))
        self.client.force_login(loner)
        self.assertContains(self.client.get(self.url), 'not assigned to a division')

    def test_strings_add_rename_delete(self):
        self.client.force_login(self.supervisor)
        self.post('add_string', new_string='New String')
        new = String.objects.get(name='New String')
        self.assertEqual(new.division, self.division_a)  # supervisor's only division
        self.post(f'rename_string:{new.id}', **{f'rename_{new.id}': 'Renamed'})
        new.refresh_from_db()
        self.assertEqual(new.name, 'Renamed')
        self.assertContains(self.post(f'rename_string:{new.id}', **{f'rename_{new.id}': 'string a'}), 'already exists')
        self.assertContains(self.post(f'delete_string:{self.string_a.id}'), 'still has training animals')
        self.post(f'delete_string:{new.id}')
        self.assertFalse(String.objects.filter(pk=new.id).exists())

    def test_only_superuser_can_set_division(self):
        self.client.force_login(self.supervisor)
        response = self.client.post(self.url, {'do': f'set_division:{self.string_a.id}', f'division_{self.string_a.id}': self.division_b.id})
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.superuser)
        self.post(f'set_division:{self.string_a.id}', **{f'division_{self.string_a.id}': self.division_b.id})
        self.string_a.refresh_from_db()
        self.assertEqual(self.string_a.division, self.division_b)

    def test_keepers_add_and_remove(self):
        self.client.force_login(self.supervisor)
        self.post(f'add_keeper:{self.string_a.id}', **{f'new_keeper_{self.string_a.id}': self.keeper.id})
        self.assertIn(self.keeper, self.string_a.keepers.all())
        self.post(f'remove_keeper:{self.string_a.id}:{self.keeper.id}')
        self.assertFalse(self.string_a.keepers.exists())

    def test_animals_add_and_delete(self):
        self.client.force_login(self.supervisor)
        self.post(f'add_animal:{self.string_a.id}', **{f'new_animal_{self.string_a.id}': 'Nety'})
        nety = TrainingAnimal.objects.get(name='Nety')
        self.assertEqual(nety.string, self.string_a)
        self.assertContains(self.post(f'add_animal:{self.string_a.id}', **{f'new_animal_{self.string_a.id}': 'ROCKY'}), 'already exists')
        self.post(f'delete_animal:{nety.id}')
        self.assertFalse(TrainingAnimal.objects.filter(pk=nety.id).exists())

    def test_behaviors_reinforcers_and_move_to_maintenance(self):
        self.client.force_login(self.supervisor)
        aid = self.animal.id
        self.post(f'add_behavior:{aid}:new', **{f'new_behavior_{aid}_new': 'Crate'})
        self.post(f'add_behavior:{aid}:maintenance', **{f'new_behavior_{aid}_maintenance': 'Target'})
        self.post(f'add_reinforcer:{aid}', **{f'new_reinforcer_{aid}': 'Grapes'})
        crate = self.animal.new_behaviors.get()
        self.assertEqual(self.animal.reinforcers.get().name, 'Grapes')

        self.post(f'move_behavior:{aid}:{crate.id}')
        self.assertFalse(self.animal.new_behaviors.exists())
        self.assertEqual(sorted(self.animal.maintenance_behaviors.values_list('name', flat=True)), ['Crate', 'Target'])
        self.assertEqual(Behavior.objects.get(name='Crate', behavior_type='maintenance').behavior_type, 'maintenance')

        target = self.animal.maintenance_behaviors.get(name='Target')
        self.post(f'remove_behavior:{aid}:maintenance:{target.id}')
        self.post(f'remove_reinforcer:{aid}:{self.animal.reinforcers.get().id}')
        self.assertEqual(self.animal.maintenance_behaviors.count(), 1)
        self.assertFalse(self.animal.reinforcers.exists())


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class WorkingDivisionTests(TestCase):

    def setUp(self):
        self.terrestrial = Division.objects.create(name='Terrestrial')
        self.aquatic = Division.objects.create(name='Aquatic')
        self.string_t = String.objects.create(name='Tiger String', division=self.terrestrial)
        self.string_a = String.objects.create(name='Penguin String', division=self.aquatic)
        ASG.objects.create(name='Tiger', string=self.string_t)
        ASG.objects.create(name='Penguins', string=self.string_a)
        group, _ = Group.objects.get_or_create(name='Supervisor')
        self.both = User.objects.create_user('both', password='pw', is_staff=True)
        self.both.groups.add(group)
        self.both.profile.divisions.add(self.terrestrial, self.aquatic)
        self.one = User.objects.create_user('one', password='pw', is_staff=True)
        self.one.groups.add(group)
        self.one.profile.divisions.add(self.terrestrial)
        self.keeper = User.objects.create_user('kay', password='pw')
        self.root = User.objects.create_superuser('rootw', 'r@example.com', 'pw')

    def pick(self, *divisions, next_url=None):
        return self.client.post(reverse('zoo:set_divisions'), {
            'division': [d.id for d in divisions], 'next': next_url or reverse('zoo:asg_list'),
        }, follow=True)

    def test_checkboxes_only_for_people_with_more_than_one_division(self):
        for user, expected in ((self.both, True), (self.root, True), (self.one, False), (self.keeper, False)):
            self.client.force_login(user)
            self.assertEqual('Working in:' in self.client.get(reverse('zoo:asg_list')).content.decode(), expected, user.username)

    def test_ticking_divisions_filters_calendars_and_manage_page(self):
        self.client.force_login(self.both)
        page = self.client.get(reverse('zoo:asg_list'))
        self.assertContains(page, 'Tiger String')
        self.assertContains(page, 'Penguin String')  # everything ticked by default

        self.pick(self.terrestrial)
        for url in (reverse('zoo:asg_list'), reverse('zoo:manage_training')):
            page = self.client.get(url)
            self.assertContains(page, 'Tiger String')
            self.assertNotContains(page, 'Penguin String')

        self.pick(self.aquatic, self.terrestrial)
        self.assertContains(self.client.get(reverse('zoo:asg_list')), 'Penguin String')

    def test_unticking_everything_is_refused(self):
        self.client.force_login(self.both)
        self.pick(self.aquatic)
        response = self.pick()
        self.assertContains(response, 'Keep at least one division ticked.')
        self.assertNotContains(self.client.get(reverse('zoo:asg_list')), 'Tiger String')  # still just Aquatic

    def test_superuser_filter_and_item_assignment_scope(self):
        self.client.force_login(self.root)
        self.pick(self.aquatic)
        page = self.client.get(reverse('zoo:asg_list'))
        self.assertNotContains(page, 'Tiger String')
        assignment_page = self.client.get(reverse('zoo:item_assignment'))
        self.assertContains(assignment_page, 'Penguins')
        self.assertNotContains(assignment_page, '>Tiger<')

    def test_cannot_pick_a_division_you_do_not_have_or_redirect_off_site(self):
        self.client.force_login(self.one)
        response = self.client.post(reverse('zoo:set_divisions'), {'division': [self.aquatic.id], 'next': 'https://evil.example/'})
        self.assertRedirects(response, reverse('zoo:asg_list'))
        self.assertNotContains(self.client.get(reverse('zoo:asg_list')), 'Penguin String')
