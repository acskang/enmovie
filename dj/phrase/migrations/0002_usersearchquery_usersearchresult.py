# Generated by Django 5.2 on 2025-07-07 01:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phrase', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSearchQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_query', models.CharField(db_index=True, max_length=500)),
                ('translated_query', models.CharField(blank=True, max_length=500, null=True)),
                ('search_count', models.IntegerField(default=1)),
                ('last_searched_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('result_count', models.IntegerField(default=0)),
                ('has_results', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-last_searched_at'],
                'indexes': [models.Index(fields=['original_query'], name='phrase_user_origina_6f8d93_idx'), models.Index(fields=['translated_query'], name='phrase_user_transla_f63801_idx'), models.Index(fields=['-last_searched_at'], name='phrase_user_last_se_90852d_idx')],
            },
        ),
        migrations.CreateModel(
            name='UserSearchResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relevance_score', models.FloatField(default=1.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('movie_quote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='search_results', to='phrase.moviequote')),
                ('search_query', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='phrase.usersearchquery')),
            ],
            options={
                'ordering': ['-relevance_score', '-created_at'],
                'unique_together': {('search_query', 'movie_quote')},
            },
        ),
    ]
