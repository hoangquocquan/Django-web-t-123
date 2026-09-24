"""Staging settings that preserve the production runtime contract.

Staging deliberately inherits every security and dependency requirement from
production.  The only difference is the environment label used by health and
observability reports, so a staging result cannot be mistaken for production.
"""

from .production import *  # noqa: F403


ENVIRONMENT = "staging"
