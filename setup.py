from setuptools import setup, find_packages

setup(
    name='ktg_storage',            # The name of your app
    version='0.1.0',               # Version of your app
    packages=find_packages(),      # Automatically find packages in the app directory
    include_package_data=True,     # Include additional files specified in MANIFEST.in
    install_requires=[             # List dependencies your app needs
        'django>=3.0',
    ],
    description='A reusable Django app for managing storage functionality',
    # Long description from README file
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',  # Markdown format for README
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/KayakTech/ktg_storage',  # URL for your GitHub repo
    classifiers=[  # Classifiers for Python packages
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
    ],
)
