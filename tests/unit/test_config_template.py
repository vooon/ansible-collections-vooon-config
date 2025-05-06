"""
Test config_template funcs
"""

import pathlib
import sys

import pytest  # noqa

actions_path = pathlib.Path(__file__).parent / ".." / ".." / "plugins" / "action"
sys.path.insert(0, str(actions_path.absolute()))

import config_template  # noqa

INI_REPEATED_OPTS = """\
[DEFAULT]

#
# From nova.conf
#

#default_availability_zone = nova
default_availability_zone = zone1



[pci]
alias = foo
alias = bar
alias = baz

multiline =
 foo
   bar
     baz
"""

INI_EDITIED_OPTS = """\
[DEFAULT]

#
# From nova.conf
#

#default_availability_zone = nova
default_availability_zone = zone1

[pci]
alias = quux
        zuul

multiline =
 foo
   bar
     baz

[filter_scheduler]
available_filters = nova.scheduler.filters.all_filters
        extra.all_filters
"""

INI_CEPH_OPTS = """\
# FishOS Deployer managed

[global]
  public network = 10.10.40.0/23
  cluster network = 10.10.50.0/23
  fsid = f15f8fff-d594-4e07-a104-a018f90385dc
  auth cluster required = cephx
  auth service required = cephx
  auth client required = cephx
  max open files = 131072
  mon_max_pg_per_osd = 200
  osd journal size = 1024
  osd pool default size = 3
  osd pool default min size = 2
  osd pool default pg num = 32
  osd pool default pgp num = 32
  osd crush chooseleaf type = 1
  mon initial members = p316, p317, p318

[mon.p316]
  host = p316
  # NOTE(vermakov) = for default ports we may omit them
  # https = //docs.ceph.com/docs/nautilus/rados/configuration/msgr2/
  mon addr = 10.10.40.17
  #mon addr = [v2:10.10.40.17:3300/0,v1:10.10.40.17:6789/0]
"""

INI_EDITIED_CEPH_OPTS = """\
# FishOS Deployer managed

[global]
  public network = 0.0.0.0/0
  cluster network = 10.10.50.0/23
  fsid = f15f8fff-d594-4e07-a104-a018f90385dc
  auth cluster required = cephx
  auth service required = cephx
  auth client required = cephx
  max open files = 131072
  mon_max_pg_per_osd = 200
  osd journal size = 1024
  osd pool default size = 3
  osd pool default min size = 2
  osd pool default pg num = 32
  osd pool default pgp num = 32
  osd crush chooseleaf type = 1
  mon initial members = p316, p317, p318
new unindented option = foo,bar
  new indented option = baz,quux

[mon.p316]
  host = p316
  # NOTE(vermakov) = for default ports we may omit them
  # https = //docs.ceph.com/docs/nautilus/rados/configuration/msgr2/
  mon addr = 10.10.40.17
  #mon addr = [v2:10.10.40.17:3300/0,v1:10.10.40.17:6789/0]

[client]
  rbd cache = True
"""

ENV_OPTS = """\
# Configuration file path of corosync
# Default : /etc/corosync/corosync.conf
HA_CONF="/etc/corosync/corosync.conf"

LOG_LEVEL="info"
"""

ENV_EDITIED_OPTS = """\
# Configuration file path of corosync
# Default : /etc/corosync/corosync.conf
HA_CONF="/etc/corosync/corosync.conf"

LOG_LEVEL="debug"
"""

IRONIC_CMDLINE_OPTS = """\
[pxe]
kernel_append_params = nofb nomodeset vga=normal sshkey="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDnLJU+MSA3BL/yyWjF6QyDlhXAA0j6upftEZpL1ATYe ipa@ironic"
"""

IRONIC_CMDLINE_EDITIED_OPTS = """\
[pxe]
kernel_append_params = nofb nomodeset vga=normal sshkey="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDnLJU+MSA3BL/yyWjF6QyDlhXAA0j6upftEZpL1ATYe ipa@ironic"

[ilo]
verify_ca = False
"""


def test_iniparse_merge_repeated_options():
    config = config_template.INIConfig.from_string(
        INI_REPEATED_OPTS, "INI_REPEATED_OPTS"
    )

    config.merge_repeated_options()

    assert config.to_string() == INI_REPEATED_OPTS
    assert config["DEFAULT"]["default_availability_zone"] == "zone1"
    assert config["pci"]["alias"] == "foo\nbar\nbaz"
    assert config["pci"]["multiline"] == "\nfoo\nbar\nbaz"

    config["filter_scheduler"]["available_filters"] = (
        "nova.scheduler.filters.all_filters\nextra.all_filters"
    )
    config["pci"]["alias"] = "quux\nzuul"

    config.tidy()
    assert config.to_string() == INI_EDITIED_OPTS


def test_iniparse_ceph():
    config = config_template.INIConfig.from_string(INI_CEPH_OPTS, "INI_CEPH_OPTS")

    assert config.to_string() == INI_CEPH_OPTS

    d = config.as_dict()
    assert d["global"]["public network"] == "10.10.40.0/23"

    config["global"]["public network"] = "0.0.0.0/0"
    config.set_option("global", "new unindented option", ["foo", "bar"])
    config.set_option("global", "  new indented option", ["baz", "quux"])
    config.set_option("client", "  rbd cache", True)

    assert config.to_string() == INI_EDITIED_CEPH_OPTS


def test_iniparse_env():
    ln = config_template.OptionLine.parse('LOG_LEVEL="info"')

    assert ln is not None
    assert ln.name == "LOG_LEVEL"
    assert ln.value == '"info"'

    config = config_template.INIConfig.from_string(ENV_OPTS, "ENV_OPTS")

    assert config.to_string() == ENV_OPTS
    assert config["DEFAULT"]["LOG_LEVEL"] == '"info"'

    d = config.as_dict()
    assert d != {}
    assert d["DEFAULT"]["LOG_LEVEL"] == '"info"'

    config.set_option("DEFAULT", "LOG_LEVEL", '"debug"')

    assert config.to_string() == ENV_EDITIED_OPTS


def test_iniparse_ironic_cmdline():
    ln = config_template.OptionLine.parse(
        'kernel_append_params = nofb nomodeset vga=normal sshkey="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDnLJU+MSA3BL/yyWjF6QyDlhXAA0j6upftEZpL1ATYe ipa@ironic"'
    )

    assert ln is not None
    assert ln.name == "kernel_append_params"
    assert (
        ln.value
        == 'nofb nomodeset vga=normal sshkey="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDnLJU+MSA3BL/yyWjF6QyDlhXAA0j6upftEZpL1ATYe ipa@ironic"'
    )

    config = config_template.INIConfig.from_string(
        IRONIC_CMDLINE_OPTS, "IRONIC_CMDLINE_OPTS"
    )

    assert config.to_string() == IRONIC_CMDLINE_OPTS

    d = config.as_dict()
    assert d != {}

    config.set_option("ilo", "verify_ca", False)

    assert config.to_string() == IRONIC_CMDLINE_EDITIED_OPTS
