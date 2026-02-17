# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0


from jinja2.filters import pass_context


@pass_context
def argsenvfmt(context, text, quote=True, multiline=True):
    """Format multi-line arguments/options to a single line for using in systemd's EnvironmetFile"""

    lines = (line.strip() for line in text.splitlines())
    if not multiline:
        combined = " ".join(line for line in lines if line)

        if not quote:
            return combined

        quote = context.environment.filters["quote"]
        return quote(combined)

    newlines = ['"\\']
    for line in lines:
        if quote:
            line = line.replace('"', '\\"')
        newlines.append(line + " \\")
    newlines.append('"')

    return "\n".join(newlines)


class FilterModule:
    """Ansible argsenvfmt jinja2 filters"""

    def filters(self):
        return {
            "argsenvfmt": argsenvfmt,
        }
