"""
Kinetic Python SDK

A Python SDK for interacting with the Kinetic protocol (a Compound v2 fork) on Flare.
"""

from .kinetic_sdk import KineticSDK
from .constants import KINETIC_ADDRESSES, KINETIC_TOKENS

__all__ = ['Kinetic', 'KineticSDK', 'KINETIC_ADDRESSES', 'KINETIC_TOKENS']
__version__ = '0.1.0' 