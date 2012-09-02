from setuptools import setup, find_packages
setup(
    name = "nose-profile",
    version = '1.0',
    author = "The SIO2 Project Team",
    author_email = 'sio2@sio2project.mimuw.edu.pl',
    description = "Calltree coverage plugin for nose",
    url = 'https://github.com/sio2project/nose-profile',
    license = 'GPL',

    packages = find_packages(),

    install_requires = [
        'coverage >= 3.3.1',
        'nose >= 0.11.1',
    ],

    entry_points = {
        'nose.plugins': [
            'calltree = nose_profile:CallTree',
        ],
    }
)

