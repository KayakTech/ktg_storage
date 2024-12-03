from setuptools import setup, find_packages

setup(
    name='ktg_storage',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'asgiref==3.8.1',
        'boto3==1.24.7',
        'botocore==1.27.7',
        'Django==4.2.5',
        'django-cors-headers==3.14.0',
        'djangorestframework==3.14.0',
        'djangorestframework-simplejwt==5.2.2',
        'drf-yasg==1.21.5',
        'inflection==0.5.1',
        'jmespath==1.0.1',
        'packaging==24.2',
        'PyJWT==2.9.0',
        'python-dateutil==2.8.2',
        'python-dotenv==1.0.1',
        'pytz==2024.2',
        'PyYAML==6.0.2',
        's3transfer==0.6.2',
        'setuptools==75.4.0',
        'sqlparse==0.5.1',
        'typing_extensions==4.12.2',
        'uritemplate==4.1.1',
        'urllib3==1.26.20',
        "django-storages==1.14.4",
    ],
    description='A reusable Django app for managing storage functionality',

    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Kayak Technology Group',
    author_email='info@kayaktechgroup.com',
    url='https://github.com/KayakTech/ktg_storage',
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12.7',
        'License :: OSI Approved :: MIT License',
    ],
)
