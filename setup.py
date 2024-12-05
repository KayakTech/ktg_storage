from setuptools import setup, find_packages

setup(
    name='ktg_storage',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[

        'boto3==1.24.7',
        'botocore==1.27.7',
        'Django==4.2.5',
        'djangorestframework==3.14.0',
        'PyJWT==2.9.0',
        'pytz==2024.2',
        'PyYAML==6.0.2',
        's3transfer==0.6.2',
        'typing_extensions==4.12.2',
        "django-storages==1.14.4",
        "moviepy==1.0.3",
        "pillow==11.0.0",
        "PyMuPDF==1.24.14",
        "python-magic==0.4.27",
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
