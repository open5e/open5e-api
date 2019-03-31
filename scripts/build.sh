#!/bin/bash
# To create a releaseable deployment package (do this before check-in.):

# Make sure all dependencies are listed correctly.  This command outputs requirements.txt.
pipenv lock -r

