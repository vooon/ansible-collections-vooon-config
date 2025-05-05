# Copyright: (c) 2015, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# https://github.com/luqasn/ansible_jsonnet_template_action

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import shutil
import stat
import tempfile
import _jsonnet
import yaml
import json

from ansible import constants as C
from ansible.config.manager import ensure_type
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleAction, AnsibleActionFail
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase
from ansible.template import generate_ansible_template_vars


# make yaml prettier
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def import_callback(self, dirs, rel):
        for d in dirs:
            try:
                full_path = self._find_needle(d, rel)
                with open(full_path) as f:
                    return full_path, f.read()
            except AnsibleError:
                continue

        raise AnsibleError("Unable to find '%s' in expected paths." % to_native(needle))

    def run(self, tmp=None, task_vars=None):
        ''' handler for template operations '''

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Options type validation
        # stings
        for s_type in ('src', 'dest', 'state'):
            if s_type in self._task.args:
                value = ensure_type(self._task.args[s_type], 'string')
                if value is not None and not isinstance(value, string_types):
                    raise AnsibleActionFail("%s is expected to be a string, but got %s instead" % (s_type, type(value)))
                self._task.args[s_type] = value

        # booleans
        try:
            follow = boolean(self._task.args.get('follow', False), strict=False)
        except TypeError as e:
            raise AnsibleActionFail(to_native(e))

        # assign to local vars for ease of use
        source = self._task.args.get('src', None)
        dest = self._task.args.get('dest', None)
        state = self._task.args.get('state', None)
        format = self._task.args.get('format', 'json')
        include_dir = self._task.args.get('include_dir', 'templates')

        output_encoding = self._task.args.get('output_encoding', 'utf-8') or 'utf-8'

        try:
            # logical validation
            if state is not None:
                raise AnsibleActionFail("'state' cannot be specified on a template")
            elif source is None or dest is None:
                raise AnsibleActionFail("src and dest are required")
            elif format not in ['json', 'yaml']:
                raise AnsibleActionFail("format needs to be either json or yaml")
            else:
                try:
                    source = self._find_needle('templates', source)
                except AnsibleError as e:
                    raise AnsibleActionFail(to_text(e))

            mode = self._task.args.get('mode', None)
            if mode == 'preserve':
                mode = '0%03o' % stat.S_IMODE(os.stat(source).st_mode)

            # Get vault decrypted tmp file
            try:
                tmp_source = self._loader.get_real_file(source)
            except AnsibleFileNotFound as e:
                raise AnsibleActionFail("could not find src=%s, %s" % (source, to_text(e)))
            b_tmp_source = to_bytes(tmp_source, errors='surrogate_or_strict')

            # template the source data locally & get ready to transfer
            try:
                with open(b_tmp_source, 'rb') as f:
                    try:
                        template_data = to_text(f.read(), errors='surrogate_or_strict')
                    except UnicodeError:
                        raise AnsibleActionFail("Template source files must be utf-8 encoded")

                # # add ansible 'template' vars
                temp_vars = task_vars.copy()
                # temp_vars.update(generate_ansible_template_vars(source, dest))
                string_vars = { key:str(value) for (key,value) in temp_vars.items()}

                resultant = _jsonnet.evaluate_snippet(
                    source,
                    template_data,
                    ext_vars=string_vars,
                    import_callback=lambda dir, rel: self.import_callback([dir, include_dir], rel),
                )
                if format == 'yaml':
                    resultant = yaml.dump(json.loads(resultant), allow_unicode=True)
            except AnsibleAction:
                raise
            except Exception as e:
                raise AnsibleActionFail("%s: %s" % (type(e).__name__, to_text(e)))
            finally:
                self._loader.cleanup_tmp_file(b_tmp_source)

            new_task = self._task.copy()
            # mode is either the mode from task.args or the mode of the source file if the task.args
            # mode == 'preserve'
            new_task.args['mode'] = mode

            # remove 'template only' options:
            for remove in ('output_encoding', 'format', 'include_dir'):
                new_task.args.pop(remove, None)

            local_tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)

            try:
                result_file = os.path.join(local_tempdir, os.path.basename(source))
                with open(to_bytes(result_file, errors='surrogate_or_strict'), 'wb') as f:
                    f.write(to_bytes(resultant, encoding=output_encoding, errors='surrogate_or_strict'))

                new_task.args.update(
                    dict(
                        src=result_file,
                        dest=dest,
                        follow=follow,
                    ),
                )
                copy_action = self._shared_loader_obj.action_loader.get('copy',
                                                                        task=new_task,
                                                                        connection=self._connection,
                                                                        play_context=self._play_context,
                                                                        loader=self._loader,
                                                                        templar=self._templar,
                                                                        shared_loader_obj=self._shared_loader_obj)
                result.update(copy_action.run(task_vars=task_vars))
            finally:
                shutil.rmtree(to_bytes(local_tempdir, errors='surrogate_or_strict'))

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
