from Testing import ZopeTestCase

# Let Zope know about the two products we require above-and-beyond a basic
# Plone install (PloneTestCase takes care of these).
ZopeTestCase.installProduct('Relations')
ZopeTestCase.installProduct('PloneOntology')

# Import PloneTestCase - this registers more products with Zope as a side effect
from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite

# Set up a Plone site, and apply the membrane and borg extension profiles
# to make sure they are installed.
setupPloneSite(products=('Relations', 'PloneOntology'))

class PloneOntologyTestCase(PloneTestCase):
    """Base class for integration tests for the 'PloneOntology' product.
    """

class PloneOntologyFunctionalTestCase(FunctionalTestCase):
    """Base class for functional integration tests for the 'PloneOntology' product.
    """