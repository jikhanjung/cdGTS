from django.db import migrations


def set_kinds(apps, schema_editor):
    Release = apps.get_model("releases", "Release")
    # Scratch verify releases were keyed graph:<slug>; everything else is a published release.
    Release.objects.filter(version__startswith="graph:").update(kind="transient")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("releases", "0004_alter_release_options_release_kind_and_more"),
    ]

    operations = [
        migrations.RunPython(set_kinds, noop),
    ]
