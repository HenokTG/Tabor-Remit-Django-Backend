# Generated by Django 4.0.3 on 2022-10-16 12:10

from django.db import migrations, models
import django.utils.timezone
import model_helpers.upload_to_helpers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForexRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('from_currency', models.CharField(default='USD', max_length=10)),
                ('to_currency', models.CharField(default='ETB', max_length=10)),
                ('forex_rate', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NewsUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('news_title', models.CharField(blank=True, max_length=150, null=True)),
                ('news_content', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('reciever_agent', models.CharField(blank=True, max_length=150, null=True)),
                ('notice', models.CharField(blank=True, max_length=255, null=True)),
                ('is_viewed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentsTracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('payment_type', models.CharField(blank=True, max_length=150, null=True)),
                ('payment_bank', models.CharField(blank=True, max_length=150, null=True)),
                ('transaction_number', models.CharField(blank=True, max_length=150, null=True)),
                ('paid_amount', models.FloatField(blank=True, null=True)),
                ('total_payment', models.FloatField(blank=True, null=True)),
                ('agent_name', models.CharField(blank=True, max_length=150, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AgentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('agent_name', models.CharField(max_length=50, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to=model_helpers.upload_to_helpers.upload_to)),
                ('business_name', models.CharField(blank=True, max_length=150, null=True)),
                ('commission', models.FloatField(blank=True, max_length=10, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('phone', models.BigIntegerField(blank=True, null=True)),
                ('region', models.CharField(blank=True, max_length=100, null=True)),
                ('zone', models.CharField(blank=True, max_length=100, null=True)),
                ('woreda', models.CharField(blank=True, max_length=100, null=True)),
                ('street', models.CharField(blank=True, max_length=100, null=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
