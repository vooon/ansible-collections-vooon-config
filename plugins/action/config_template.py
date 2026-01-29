# (c) 2015, Kevin Carter <kevin.carter@rackspace.com>
# (c) 2023, Vladimir Ermakov <vermakov@sardinasystems.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
# NOTE(vermakov): this is slightly modified version of the plugin.
# Changes:
# 1. Dropped support for Python 2 and Ansible 2.9. We're running on 2.14+
# 2. Changed Diff back to unified file diff
# 3. Changed to use iniparser instead of usage of outdated RawConfigParser

import base64
import dataclasses
import json
import os
import re
import shutil
import tempfile
import typing
from io import StringIO

import hjson
import tomlkit
from ansible import constants as C
from ansible.config.manager import ensure_type
from ansible.errors import AnsibleAction, AnsibleActionFail, AnsibleError
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase
from ansible.template import generate_ansible_template_vars
from iniparse import ini
from iniparse.utils import tidy as ini_tidy
from jsonpatch import JsonPatch
from ruamel.yaml import YAML

try:
    from ansible.template import AnsibleEnvironment
except ImportError:
    # for ansible-core > 2.20
    from jinja2.environment import Environment as AnsibleEnvironment

_DocT = typing.Union[dict, list]


class OptionLine(ini.OptionLine):
    indent = ""

    regex = re.compile(
        r"^(?P<indent>[\s]*)"
        r"(?P<name>[^:=\s[][^:=]*)"
        r"(?P<sep>[:=]\s*)"
        r"(?P<value>.*)$"
    )

    indent_regex = re.compile(r"^(?P<indent>[\s]*)")

    def to_string(self) -> str:
        return self.indent + super().to_string()

    @classmethod
    def parse(cls, line: str) -> typing.Optional["OptionLine"]:
        instance = super().parse(line)
        if instance is not None:
            m = cls.indent_regex.match(line)
            if m:
                instance.indent = m.group("indent")

        return instance


class INIConfig(ini.INIConfig):
    _line_types = [
        ini.EmptyLine,
        ini.CommentLine,
        ini.SectionLine,
        OptionLine,
        ini.ContinuationLine,
    ]
    _injected_default_section: bool = False

    @classmethod
    def from_string(
        cls, resultant: str, source: str = "<???>", **kwargs
    ) -> "INIConfig":
        if resultant.endswith("\n"):
            resultant = resultant[0:-1]

        ini.DEFAULTSECT = "@@disable_default_section_special_handling"
        ini.change_comment_syntax(";#", allow_rem=False)

        buf = StringIO(resultant)
        buf.name = source

        try:
            instance = cls(buf, optionxformvalue=str, **kwargs)
        except ini.MissingSectionHeaderError:
            # Fallback for .env like files used by systemd
            buf.seek(0)
            buf.write("[DEFAULT]\n")
            buf.write(resultant)
            buf.seek(0)

            instance = cls(buf, optionxformvalue=str, **kwargs)
            instance._injected_default_section = True

        return instance

    def to_string(self) -> str:
        resultant = str(self)
        if self._injected_default_section:
            resultant = "\n".join(resultant.splitlines()[1:])

        if not resultant.endswith("\n"):
            resultant += "\n"

        return resultant

    def merge_repeated_options(self) -> None:
        for section_name in list(self):
            section = self[section_name]
            for container in section._lines:
                if not isinstance(container, ini.LineContainer):
                    continue

                to_drop: typing.List[int] = []
                for idx, line in enumerate(container.contents):
                    if not isinstance(line, ini.LineContainer):
                        continue

                    opt = section._options[line.get_name()]
                    if line is not opt:
                        to_drop.append(idx)
                        opt.extend(line.contents)
                        opt.contents.sort(key=lambda x: x.line_number)

                for idx in sorted(to_drop, reverse=True):
                    del container.contents[idx]

    def tidy(self):
        ini_tidy(self)

    def as_dict(self) -> typing.Dict[str, dict]:
        def yield_section(
            sect,
        ) -> typing.Generator[typing.Tuple[str, dict], None, None]:
            for name in sect:
                v = sect[name]
                if isinstance(v, string_types) and "\n" in v:
                    yield name, v.splitlines()
                    continue
                yield name, v

        return {section: dict(yield_section(self[section])) for section in self}

    def set_option(
        self,
        section: str,
        key: str,
        value: typing.Any,
        args: typing.Optional["TaskArgs"] = None,
    ):
        if args is None:
            args = TaskArgs()

        if isinstance(value, list):
            value = args.ini_list_sep.join(to_text(item) for item in value)
        elif isinstance(value, dict):
            value = json.dumps(value, sort_keys=True)

        xkey = key.strip()
        ind_idx = key.index(xkey)
        if ind_idx > 0:
            indent = key[0:ind_idx]

            if section not in self:
                self._new_namespace(section)

            sec = self[section]
            if xkey in sec:
                sec[xkey] = value  # keep indentation
            else:
                # See ini.INISection.__setitem__
                ol = OptionLine(xkey, value)
                ol.indent = indent
                obj = ini.LineContainer(ol)
                sec._lines[-1].add(obj)
                sec._options[xkey] = obj

        else:
            self[section][key] = value


@dataclasses.dataclass
class SimpleMerger:
    new_items: _DocT
    list_extend: bool = True
    yml_multilines: bool = False

    def apply(self, base_items: _DocT, in_place: bool = True) -> _DocT:
        """Recursively merge new_items into base_items."""
        if isinstance(self.new_items, dict):
            for key, value in self.new_items.items():
                if isinstance(value, dict):
                    base_items[key] = SimpleMerger(
                        value, self.list_extend, self.yml_multilines
                    ).apply(
                        base_items.get(key, {})  # type: ignore
                    )

                elif not isinstance(value, int) and (
                    "," in value or ("\n" in value and not self.yml_multilines)
                ):
                    base_items[key] = re.split(",|\n", value)
                    base_items[key] = [i.strip() for i in base_items[key] if i]
                elif isinstance(value, list):
                    if isinstance(base_items.get(key), list) and self.list_extend:  # type: ignore
                        base_items[key].extend(value)
                    else:
                        base_items[key] = value
                elif isinstance(value, (tuple, set)):
                    if isinstance(base_items.get(key), tuple) and self.list_extend:  # type: ignore
                        base_items[key] += tuple(value)
                    elif isinstance(base_items.get(key), list) and self.list_extend:  # type: ignore
                        base_items[key].extend(list(value))
                    else:
                        base_items[key] = value
                else:
                    base_items[key] = self.new_items[key]

        elif isinstance(self.new_items, list):
            if self.list_extend:
                base_items.extend(self.new_items)  # type: ignore
            else:
                base_items = self.new_items

        return base_items


@dataclasses.dataclass
class TaskArgs:
    source: str = None  # type: ignore # src or temp file
    dest: str = None  # type: ignore # remote path, type: ignore
    src: str = None  # type: ignore # local template file, type: ignore
    remote_src: bool = False  # use remote file as source
    content: typing.Any = None  # content, will be placed to temp file
    config_overrides: typing.Optional[_DocT] = None
    config_type: str = "ini"
    searchpath: list = dataclasses.field(default_factory=list)
    list_extend: bool = False
    ignore_none_type: bool = False
    default_section: str = "DEFAULT"
    ini_list_sep: str = ","
    ini_tidy: bool = True
    json_indent: int = 4
    json_sort_keys: bool = True
    yml_multilines: bool = False  # maybe unsupported
    yaml_indent_mapping: int = 2
    yaml_indent_sequence: int = 4
    yaml_indent_offset: int = 2
    strip_comments: bool = False
    block_start_string: str = None  # type: ignore
    block_end_string: str = None  # type: ignore
    variable_start_string: str = None  # type: ignore
    variable_end_string: str = None  # type: ignore
    comment_start_string: str = None  # type: ignore
    comment_end_string: str = None  # type: ignore
    render_template: bool = True
    state: str = None  # type: ignore # should not be set
    _patcher: typing.Union[None, SimpleMerger, JsonPatch] = None

    @classmethod
    def from_args(cls, task_args: dict) -> "TaskArgs":
        def yiled_args() -> typing.Generator[typing.Tuple[str, typing.Any], None, None]:
            for field in dataclasses.fields(cls):
                v = task_args.get(field.name, field.default)
                if isinstance(field.type, bool):
                    yield field.name, boolean(v, strict=False)
                elif isinstance(field.type, string_types) and v is not None:
                    yield field.name, ensure_type(v, "string")
                elif isinstance(field.type, int) and v is not None:
                    yield field.name, ensure_type(v, "integer")
                elif v is not None:
                    yield field.name, v

        return cls(**dict(yiled_args()))


class ActionModule(ActionBase):
    TRANSFERS_FILES = True

    def type_merger(self, resultant: str, args: TaskArgs) -> typing.Tuple[str, _DocT]:
        if args.config_type == "ini":
            return self.return_config_overrides_ini(resultant, args)
        elif args.config_type == "json":
            return self.return_config_overrides_json(resultant, args, json.loads)
        elif args.config_type == "hjson":
            return self.return_config_overrides_json(resultant, args, hjson.loads)
        elif args.config_type == "yaml":
            return self.return_config_overrides_yaml(resultant, args)
        elif args.config_type == "toml":
            return self.return_config_overrides_toml(resultant, args)
        else:
            raise ValueError("Unsupported config_type")

    def return_config_overrides_ini(
        self, resultant: str, args: TaskArgs
    ) -> typing.Tuple[str, _DocT]:
        """Returns string value from a modified config file and dict of merged config"""
        config = INIConfig.from_string(resultant, args.source)
        config.merge_repeated_options()

        if isinstance(args._patcher, SimpleMerger):
            assert isinstance(args.config_overrides, dict)
            for section, items in args.config_overrides.items():
                # If the items value is not a dictionary it is assumed that the
                #  value is a default item for this config type.
                if not isinstance(items, dict):
                    config.set_option(args.default_section, section, items, args)
                else:
                    for key, value in items.items():
                        config.set_option(section, key, value, args)

        elif isinstance(args._patcher, JsonPatch):
            base_items = config.as_dict()
            args._patcher.apply(base_items, in_place=True)
            for section, items in base_items.items():
                for key, value in items.items():
                    config.set_option(section, key, value, args)

        if args.ini_tidy:
            config.tidy()

        return config.to_string(), config.as_dict()

    def return_config_overrides_json(
        self,
        resultant: str,
        args: TaskArgs,
        loads: typing.Callable[[typing.Any], typing.Any],
    ) -> typing.Tuple[str, _DocT]:
        """Returns config json and dict of merged config

        Its important to note that file ordering will not be preserved as the
        information within the json file will be sorted by keys.
        """
        original_resultant = loads(resultant)
        merged_resultant = self._patch(args, original_resultant)
        indent = args.json_indent if args.json_indent > 0 else None
        return (
            json.dumps(
                merged_resultant,
                indent=indent,
                sort_keys=args.json_sort_keys,
            ),
            merged_resultant,
        )

    def return_config_overrides_yaml(
        self, resultant: str, args: TaskArgs
    ) -> typing.Tuple[str, _DocT]:
        """Return config yaml and dict of merged config"""
        yaml = YAML(typ=args.strip_comments and "safe" or "rt")  # type: ignore
        yaml.default_flow_style = False
        yaml.indent(
            mapping=args.yaml_indent_mapping,
            sequence=args.yaml_indent_sequence,
            offset=args.yaml_indent_offset,
        )

        if not args.strip_comments:
            # NOTE(vermakov): see bigbang pwgen:
            # hide document start to preserve comments before it
            resultant, sep_count = re.subn(
                r"^---$",
                "#marker:---",
                resultant,
                flags=re.MULTILINE,
            )
            assert sep_count in [
                0,
                1,
            ], "More than one YAML document separator is not supported!"

        original_resultant = yaml.load(StringIO(resultant)) or {}
        merged_resultant = self._patch(args, original_resultant)

        out = StringIO()
        yaml.dump(merged_resultant, out)
        resultant = out.getvalue()
        if not args.strip_comments:
            # restore document start marker
            resultant = re.sub(
                r"^#marker:---$",
                "---",
                resultant,
                flags=re.MULTILINE,
            )

        return (
            resultant,
            merged_resultant,
        )

    def return_config_overrides_toml(
        self, resultant: str, args: TaskArgs
    ) -> typing.Tuple[str, _DocT]:
        """Returns config toml and dict of merged config"""
        original_resultant = tomlkit.loads(resultant)
        merged_resultant = self._patch(args, original_resultant)
        return (
            tomlkit.dumps(
                merged_resultant,
            ),
            merged_resultant,
        )

    def _patch(self, args: TaskArgs, base_items: _DocT) -> _DocT:
        if args._patcher is not None:
            return args._patcher.apply(base_items, in_place=True)

        return base_items

    def _load_task_args(self, task_vars: dict) -> TaskArgs:
        """Return options and status from module load."""

        args = TaskArgs.from_args(self._task.args)
        if args.config_type not in ["ini", "yaml", "json", "hjson", "toml"]:
            raise AnsibleActionFail(
                "No valid [ config_type ] was provided. Valid options are"
                " ini, yaml, json, hjson or toml.",
            )

        if args.state is not None:
            raise AnsibleActionFail("template module do not support [ state ]")

        if args.remote_src:
            if not args.src:
                raise AnsibleActionFail("No user [ src ] was provided")

            slurpee = self._execute_module(
                module_name="ansible.legacy.slurp",
                module_args=dict(src=args.src),
                task_vars=task_vars,
            )
            _content = base64.b64decode(slurpee["content"])
            args.content = to_text(_content)

            fd, content_tempfile = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP)
            f = os.fdopen(fd, "wb")
            try:
                f.write(to_bytes(args.content))
            except Exception as ex:
                os.remove(content_tempfile)
                raise AnsibleActionFail("cannot save content to temp file") from ex
            finally:
                f.close()

            args.src = content_tempfile
            args.content = ""

        try:
            args.source = self._find_needle("templates", args.src)
        except AnsibleError as ex:
            raise AnsibleActionFail("failed to find template file") from ex

        searchpath = task_vars.get("ansible_search_path", [])
        searchpath.extend([self._loader._basedir, os.path.dirname(args.source)])

        args.searchpath = []
        for p in searchpath:
            args.searchpath.append(os.path.join(p, "templates"))
            args.searchpath.append(p)

        if not args.dest:
            raise AnsibleActionFail("No [ dest ] was provided")

        # Expand any user home dir specification
        user_dest = self._remote_expand_user(args.dest)
        if user_dest.endswith(os.path.sep):
            user_dest = os.path.join(user_dest, os.path.basename(args.source))

        args.dest = user_dest

        # Default - nothing to do
        # if args.config_overrides is None:
        #     args.config_overrides = {}

        if isinstance(args.config_overrides, list):
            args._patcher = JsonPatch(args.config_overrides)

        elif isinstance(args.config_overrides, dict):
            args._patcher = SimpleMerger(
                new_items=args.config_overrides,
                list_extend=args.list_extend,
                yml_multilines=args.yml_multilines,
            )

        return args

    def run(self, tmp=None, task_vars=None):
        """Run the method"""

        if task_vars is None:
            task_vars = dict()

        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        args = self._load_task_args(task_vars=task_vars)

        try:
            with open(args.source, "rb") as f:
                try:
                    template_data = to_text(f.read(), errors="surrogate_or_strict")
                except UnicodeError as ex:
                    raise AnsibleActionFail(
                        "Template source files must be utf-8 encoded"
                    ) from ex

            # add ansible template vars
            temp_vars = task_vars.copy()
            # NOTE in the case of ANSIBLE_DEBUG=1 task_vars is VarsWithSources(MutableMapping)
            # so | operator cannot be used as it can be used only on dicts
            # https://peps.python.org/pep-0584/#what-about-mapping-and-mutablemapping
            temp_vars.update(
                generate_ansible_template_vars(args.src, args.source, args.dest)
            )

            if args.render_template:
                # force templar to use AnsibleEnvironment to prevent issues with native types
                # https://github.com/ansible/ansible/issues/46169
                templar = self._templar.copy_with_new_env(
                    environment_class=AnsibleEnvironment,
                    searchpath=args.searchpath,
                    block_start_string=args.block_start_string,
                    block_end_string=args.block_end_string,
                    variable_start_string=args.variable_start_string,
                    variable_end_string=args.variable_end_string,
                    comment_start_string=args.comment_start_string,
                    comment_end_string=args.comment_end_string,
                    available_variables=temp_vars,
                )
                resultant = templar.do_template(
                    template_data,
                    preserve_trailing_newlines=True,
                    escape_backslashes=False,
                )

            else:
                resultant = template_data

        except AnsibleAction:
            raise
        except Exception as ex:
            raise AnsibleActionFail(to_text(ex)) from ex
        finally:
            if not args.src and args.source:
                os.unlink(args.source)

        resultant, config_base = self.type_merger(resultant, args)

        if args.strip_comments and args.config_type == "ini":
            lines = [
                ln
                for ln in resultant.splitlines()
                if not (ln.startswith(("#", ";")) or ln.strip() == "")
            ]

            resultant = "# " + temp_vars["ansible_managed"]
            for line in lines:
                if line.startswith("["):
                    resultant += "\n"
                resultant += line + "\n"

        new_task = self._task.copy()
        for field in dataclasses.fields(args):
            new_task.args.pop(field.name, None)

        local_tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
        try:
            result_file = os.path.join(local_tempdir, os.path.basename(args.source))
            with open(result_file, "wb") as f:
                f.write(
                    to_bytes(resultant, encoding="utf-8", errors="surrogate_or_strict")
                )

            new_task.args.update(
                dict(
                    src=result_file,
                    dest=args.dest,
                    follow=True,
                )
            )

            # call with ansible.legacy prefix to eliminate collisions with collections while still allowing local override
            copy_action = self._shared_loader_obj.action_loader.get(
                "ansible.legacy.copy",
                task=new_task,
                connection=self._connection,
                play_context=self._play_context,
                loader=self._loader,
                templar=self._templar,
                shared_loader_obj=self._shared_loader_obj,
            )
            result.update(copy_action.run(task_vars=task_vars))

        finally:
            shutil.rmtree(to_bytes(local_tempdir, errors="surrogate_or_strict"))

        # NOTE(vermakov): let's use copy diff
        # if self._play_context.diff:
        #     copy_diff = result.pop("diff", None)
        #     if copy_diff:
        #         result["diff"] = [copy_diff]
        #     else:
        #         result["diff"] = []

        #     result["diff"].append(
        #         {"prepared": json.dumps(mods, indent=4, sort_keys=True)}
        #     )

        self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
