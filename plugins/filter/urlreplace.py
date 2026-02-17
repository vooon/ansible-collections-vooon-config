# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Sardina Systems Ltd.
# SPDX-License-Identifier: Apache-2.0


import typing
from pathlib import Path
from urllib.parse import urlparse

from jinja2.filters import pass_context

from .port import port as port_flt


@pass_context
def url_replace(
    context,
    url: str,
    pathadd: typing.Optional[str] = None,
    path: typing.Optional[str] = None,
    port: typing.Union[None, str, int] = 0,
    **kwargs,
) -> str:
    """Replace URL parts, like path, port etc."""

    u = urlparse(url)

    if isinstance(port, str):
        port = port_flt(context, port)

    if (isinstance(port, int) and port > 0) or port is None:
        netloc = u.netloc.split(":", 1)
        kwargs["netloc"] = f"{netloc[0]}:{port}" if port else netloc[0]

    if pathadd:
        kwargs["path"] = str(Path(u.path) / pathadd)

    if path is not None:
        kwargs["path"] = str(Path(path))

    if kwargs:
        u = u._replace(**kwargs)

    return u.geturl()


class FilterModule:
    """Ansible jinja2 filters"""

    def filters(self):
        return {
            "url_replace": url_replace,
        }
