# To create a source distribution for the JourneyTime Project using this file:
#   1) MAKE SURE YOU ARE IN THE ROOT FOLDER OF THE PROJECT!!
#   2) python setup.py sdist --formats=gztar,zip
#
# To install the JourneyTime Project on your VM instance using the resources
# created by this file:
#   1) MAKE SURE YOU ARE IN THE ROOT FOLDER OF THE PROJECT!!
#   2) python -m pip install -e "git+https://csgitlab.ucd.ie/flintdk/comp47360_group3_raduno/@dev#egg=comp47360_group3_raduno"
#      -> python -m pip install -e "git+https://csgitlab.ucd.ie/flintdk/comp47360_group3_raduno/
#      -> @dev    (<- this is the Branch name from which you want to install, blank if 'main')
#      -> #egg=comp47360_group3_raduno"
#      
# NOTES
# To install an entire GitHub project on the VM instance you might use:
#   python -m pip install git+https://csgitlab.ucd.ie/flintdk/comp47360_group3_raduno/    
#
# BRANCHES: It is also possible to specify a “git ref” such as branch name, a commit hash or a tag name:
#   python -m pip install git+https://csgitlab.ucd.ie/flintdk/comp47360_group3_raduno/@dev
#

#************** THIS IS A WORK IN PROGRESS!!! I HAVE TESTED NOTHING FROM GITLAB YET!!!!  *****************************

from setuptools import setup
from setuptools import find_packages

# Load the README file.
# with open(file="README.md", mode="r") as readme_handle:
#     long_description = readme_handle.read()

setup(
      # Define the library name, this is what is used along with `pip install`.
      name='comp47360_group3_raduno',

      # Define the author of the repository.
      author='Tomas Kelly, Yunpeng Cheng, Boshen Fan, Colum Prendiville',

      # Define the Author's email, so people know who to reach out to.
      author_email='tomas.kelly1@ucdconnect.ie, yunpeng.cheng@ucdconnect.ie, boshen.fan@ucdconnect.ie, colum.prendiville@ucdconnect.ie',

      # Define the version of this library.
      # Read this as
      #   - MAJOR VERSION 0
      #   - MINOR VERSION 1
      #   - MAINTENANCE VERSION 0
      version='0.0.1',

      # Here is a small description of the library. This appears
      # when someone searches for the library on https://pypi.org/search.
      description='Estimate the Journey Time required for a journey on Dublin Bus',

      # I have a long description but that will just be my README
      # file, note the variable up above where I read the file.
      #long_description=long_description,

      # This will specify that the long description is MARKDOWN.
      #long_description_content_type="text/markdown",

      url='https://csgitlab.ucd.ie/flintdk/comp47360_group3_raduno/',

      # These are the dependencies the library needs in order to run.
      install_requires=[
            'flask>=2.0.3',
            'flask-sqlalchemy>=2.5.1',
            'mysql-connector-python>=8.0.0',
            'requests==2.27.1',
            'sqlalchemy==1.4.27',
            'pandas==1.4.2',
            'scikit-learn==1.0.2'
       ],

      # Here I can specify the python version necessary to run this library.
      python_requires='>=3.9',

      license='MIT',
      packages=['journeytime'],
      zip_safe=False,

      # Additional classifiers that give some characteristics about the package.
      # For a complete list go to https://pypi.org/classifiers/.
      classifiers=[

            # I can say what phase of development my library is in.
            'Development Status :: 3 - Alpha',

            # Here I'll add the audience this library is intended for.
            'Intended Audience :: Developers',
 
            # Here I'll define the license that guides my library.
            'License :: OSI Approved :: MIT License',

            # Here I'll note that package was written in English.
            'Natural Language :: English',

            # Here I'll note that any operating system can use it.
            'Operating System :: OS Independent',

            # Here I'll specify the version of Python it uses.
            #'Programming Language :: Python',
            #'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.9',

            # Here are the topics that my library covers.
            'Topic :: Education',

            ]
      
      #scripts=['jt_scheduled_tasks/jt_scheduler.sh'],

      # entry_points={
      #       'console_scripts': [
      #             'jt_dl = jt_scheduled_tasks.data_loader:main',
      #             'jt_resample = jt_scheduled_tasks.data_resampler:main'
      #       ]
      # }
)
