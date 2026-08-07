from django.db import migrations, models
import django.db.models.deletion


def preserve_person_identifiers(apps, schema_editor):
    SensitiveDataAccessLog = apps.get_model("registry", "SensitiveDataAccessLog")
    for access_log in SensitiveDataAccessLog.objects.select_related("person").iterator():
        access_log.person_identifier = access_log.person.identifier
        access_log.save(update_fields=("person_identifier",))


class Migration(migrations.Migration):
    dependencies = [
        ("registry", "0008_recipientprofile_emergency_reason_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="sensitivedataaccesslog",
            name="person_identifier",
            field=models.CharField(blank=True, db_index=True, max_length=40),
        ),
        migrations.RunPython(preserve_person_identifiers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="sensitivedataaccesslog",
            name="person",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sensitive_data_accesses",
                to="registry.person",
            ),
        ),
    ]
