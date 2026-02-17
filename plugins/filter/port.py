# -*- coding: utf-8 -*-

from collections.abc import Iterable

from ansible.errors import AnsibleFilterError, AnsibleFilterTypeError
from ansible.utils.display import Display
from jinja2.exceptions import UndefinedError
from jinja2.filters import pass_context

display = Display()


@pass_context
def port(context, key):
    """Find port for service.name"""
    if not isinstance(key, str):
        raise AnsibleFilterTypeError(f"key should be string, got: {key!r}")

    def getport(varname):
        m = context.resolve(varname)

        k = key.split(".")
        if len(k) != 2:
            raise AnsibleFilterError(
                "key should be in following format: service_name.port_name"
            )

        service_name, port_name = k
        alt_port_name = f"{port_name}_port"

        if service_name not in m:
            raise UndefinedError(f"{varname}.{service_name}")

        m2 = m[service_name]
        if port_name in m2:
            return m2[port_name]
        elif alt_port_name in m2:
            return m2[alt_port_name]

        raise UndefinedError(
            f"{varname}.{service_name}.{port_name} and "
            f"{varname}.{service_name}.{alt_port_name}"
        )

    try:
        return getport("ports_overrides")
    except UndefinedError:
        pass
    except Exception as ex:
        display.warning(f"ports_overrides exception: {type(ex)} {ex}")

    return getport("ports")


@pass_context
def add_port(context, ip_or_hosts, key):
    if not isinstance(ip_or_hosts, (str, Iterable)):
        raise AnsibleFilterTypeError(
            f"ip_or_hosts should be string or list, got: {ip_or_hosts!r}"
        )

    p = port(context, key)
    if isinstance(ip_or_hosts, str):
        return f"{ip_or_hosts}:{p}"

    return (f"{host}:{p}" for host in ip_or_hosts)


class FilterModule:
    """Ansible port jinja2 filters"""

    def filters(self):
        return {
            "port": port,
            "add_port": add_port,
        }
