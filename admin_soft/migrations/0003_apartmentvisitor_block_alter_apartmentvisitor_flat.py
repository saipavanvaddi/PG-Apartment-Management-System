# Generated by Django 4.2.8 on 2025-03-21 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin_soft', '0002_remove_apartmentvisitor_flat_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartmentvisitor',
            name='block',
            field=models.ForeignKey(default='2', on_delete=django.db.models.deletion.CASCADE, related_name='visitors', to='admin_soft.apartmentblock'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='apartmentvisitor',
            name='flat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visitors', to='admin_soft.apartmentflat'),
        ),
    ]
