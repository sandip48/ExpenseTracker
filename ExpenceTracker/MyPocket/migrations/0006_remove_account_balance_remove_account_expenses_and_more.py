# Generated by Django 4.2.19 on 2025-03-13 12:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('MyPocket', '0005_remove_account_expense_remove_account_expense_list_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='balance',
        ),
        migrations.RemoveField(
            model_name='account',
            name='expenses',
        ),
        migrations.AddField(
            model_name='account',
            name='expense',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='account',
            name='expense_list',
            field=models.ManyToManyField(blank=True, to='MyPocket.expense'),
        ),
        migrations.AlterField(
            model_name='account',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='expense',
            name='amount',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='expense',
            name='interest_rate',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='expense',
            name='monthly_expenses',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='expense',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
