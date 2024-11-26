from setuptools import setup, find_packages

setup(
    name='my_django_app',          # The name of your package
    version='0.1.0',               # Version of your app
    packages=find_packages(),      # Automatically find packages in the app directory
    include_package_data=True,     # Include additional files specified in MANIFEST.in
    install_requires=[             # Dependencies your app needs
        'django>=3.0',
    ],
    # Short description of your app
    description='A reusable Django app for XYZ functionality',
    # Long description from README file
    long_description=open('README.md').read(),
    # Specify markdown format for README
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/my_django_app',  # URL for your project
    classifiers=[  # Classifiers for PyPI (optional, but recommended)
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
    ],
)
