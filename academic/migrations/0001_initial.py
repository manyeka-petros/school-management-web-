# Generated by Django 5.2 on 2025-06-04 07:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('portalaccount', '0003_remove_studentprofile_birth_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('Form 1', 'Form 1'), ('Form 2', 'Form 2'), ('Form 3', 'Form 3'), ('Form 4', 'Form 4')], max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classrooms', to='portalaccount.teacherprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='academic.classroom')),
                ('students', models.ManyToManyField(blank=True, related_name='subjects', to='portalaccount.studentprofile')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='portalaccount.teacherprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, max_digits=5)),
                ('exam_type', models.CharField(choices=[('Midterm', 'Midterm'), ('Final', 'Final'), ('Quiz', 'Quiz')], max_length=20)),
                ('graded_at', models.DateTimeField(auto_now_add=True)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='academic.classroom')),
                ('graded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='portalaccount.teacherprofile')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='portalaccount.studentprofile')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='academic.subject')),
            ],
            options={
                'unique_together': {('student', 'subject', 'exam_type')},
            },
        ),
    ]
