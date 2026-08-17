from django.db import migrations, models


# Old purple/red palette → new lighter purple + vivid red palette.
COLOR_MAP = {
    # old purple ramp
    "#5a0891": "#a855f7",   # primary purple (deep) → light purple
    "#9a3fd1": "#c084fc",   # soft purple → softer light
    "#3a055e": "#7e22ce",   # deep purple → deeper tone of new
    "#b56bff": "#d8b4fe",   # glow → soft glow

    # old red ramp
    "#e11d2a": "#ef4444",   # red → vivid red
    "#ff4d57": "#f87171",   # soft red → soft red (lighter)
    "#8a0a14": "#991b1b",   # deep red → deep red (matched tone)
}


def recolor_projects(apps, schema_editor):
    VideoProject = apps.get_model("core", "VideoProject")
    for old, new in COLOR_MAP.items():
        VideoProject.objects.filter(cover_color__iexact=old).update(cover_color=new)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_recolor_projects"),
    ]

    operations = [
        migrations.AlterField(
            model_name="videoproject",
            name="cover_color",
            field=models.CharField(
                default="#a855f7",
                help_text="Hex fallback colour behind the thumbnail.",
                max_length=7,
            ),
        ),
        migrations.RunPython(recolor_projects, reverse_noop),
    ]
