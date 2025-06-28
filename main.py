#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is the main entry point script for the PyInstaller bundle.
It imports and runs the main function from the actual application package.
"""

from cli.crm import main

if __name__ == '__main__':
    main()
