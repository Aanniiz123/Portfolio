from django.db import migrations, models


# Mapping of OLD amber accents → new purple + red palette.
# Each card has its own cover_color (used as --accent on the thumbnail).
COLOR_MAP = {
    "#f5a524": "#5a0891",   # main amber → primary purple
    "#ffc266": "#9a3fd1",   # soft amber → soft purple
    "#b87410": "#3a055e",   # deep amber → deep purple
    "#ffe1a8": "#b56bff",   # gradient highlight → glow
}


def recolor_projects(apps, schema_editor):
    VideoProject = apps.get_model("core", "VideoProject")
    for old, new in COLOR_MAP.items():
        VideoProject.objects.filter(cover_color__iexact=old).update(cover_color=new)


def reverse_noop(apps, schema_editor):
    # No reverse mapping needed; reversing the schema change is enough.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="videoproject",
            name="cover_color",
            field=models.CharField(
                default="#5a0891",
                help_text="Hex fallback colour behind the thumbnail.",
                max_length=7,
            ),
        ),
        migrations.RunPython(recolor_projects, reverse_noop),
    ]
