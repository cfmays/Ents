from django.db import migrations

# models that are "zoo data" a division-scoped Supervisor manages in full
SUPERVISOR_ZOO_MODELS = [
    'itemcategory', 'specialconcern', 'behaviorgoal', 'behavior', 'reinforcer',
    'string', 'asg', 'animal', 'asgapproveditem', 'calendarentry',
    'trainingsession', 'behaviorscore',
]
ACTIONS = ['add', 'change', 'delete', 'view']


def _permission(Permission, ContentType, app_label, model_name, action):
    # ContentType/Permission rows for models created earlier in this same migration
    # run don't exist yet (Django only creates them via post_migrate, once, at the
    # very end of the whole `migrate` command) -- so create them ourselves here.
    ct, _ = ContentType.objects.get_or_create(app_label=app_label, model=model_name)
    perm, _ = Permission.objects.get_or_create(
        content_type=ct,
        codename=f'{action}_{model_name}',
        defaults={'name': f'Can {action} {model_name}'},
    )
    return perm


def grant_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    supervisor_group, _ = Group.objects.get_or_create(name='Supervisor')
    administrator_group, _ = Group.objects.get_or_create(name='Administrator')

    supervisor_perms = [
        _permission(Permission, ContentType, 'zoo', model, action)
        for model in SUPERVISOR_ZOO_MODELS for action in ACTIONS
    ] + [
        _permission(Permission, ContentType, 'ents', 'enrichment', action)
        for action in ACTIONS
    ]
    supervisor_group.permissions.set(supervisor_perms)

    administrator_perms = [
        _permission(Permission, ContentType, 'auth', 'user', action)
        for action in ('add', 'change', 'view')
    ] + [
        _permission(Permission, ContentType, 'zoo', 'profile', action)
        for action in ('change', 'view')
    ] + [
        _permission(Permission, ContentType, 'zoo', 'division', action)
        for action in ACTIONS
    ]
    administrator_group.permissions.set(administrator_perms)


def revert_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Supervisor').update()  # no-op, keep the group
    Group.objects.filter(name='Administrator').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('zoo', '0004_division_profile_divisions_string_division'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(grant_permissions, revert_permissions),
    ]
