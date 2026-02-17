# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0


def whitespacefix(text):
    """Filter out multiple empty lines"""

    lines = (line.rstrip() for line in text.splitlines())

    prev = ""
    newlines = []
    for line in lines:
        if line == "" and prev == "":
            continue

        newlines.append(line)
        prev = line

    return "\n".join(newlines)


class FilterModule:
    """Ansible whitespacefix jinja2 filters"""

    def filters(self):
        return {
            "whitespacefix": whitespacefix,
        }
