#!/usr/bin/env python3
# Copyright (c) 2024 The Brave Authors. All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
"""# 🚀Brockit! Guide

```
⠀⠀⠀⠀⠀⢀⣴⣶⣶⣶⣶⣶⣶⣶⣶⣦⡀⠀⠀⠀⠀⠀
⠀⣀⣤⣤⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣤⣤⣀⠀                              🚀
⣾⣿⣿⣿⣿⡿⠛⠻⠿⠋⠁⠈⠙⠛⠛⠛⢿⣿⣿⣿⣿⣷                         .
⢈⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣿⣿⣿⡁                     .
⣿⣿⣟⠁⠀⠴⣿⣿⣿⡄⠀⠀⢠⣿⣿⣿⠦⠀⠈⣻⣿⣿                .
⣿⣿⣿⣧⡀⠀⠀⠀⣽⠇⠀⠀⠸⣯⠀⠀⠀⢀⣴⣿⣿⣿             .
⠸⣿⣿⣿⣿⣄⠀⢼⣯⣀⠀⠀⣀⣽⡧⠀⢠⣾⣿⣿⣿⠇          .
⠀⣿⣿⣿⣿⡟⠀⠀⠉⢻⣿⣿⡟⠉⠀⠀⢹⣿⣿⣿⣿⠀        .
⠀⢹⣿⣿⣿⣧⣀⣀⣤⣾⣿⣿⣷⣤⣀⣀⣴⣿⣿⣿⡏⠀      .
⠀⠈⣿⣿⣿⣿⣿⣿⣿⠛⠋⠙⠛⣿⣿⣿⣿⣿⣿⣿⠁⠀     .
⠀⠀⠸⣿⣿⣿⣿⣿⣿⣷⣤⣠⣾⣿⣿⣿⣿⣿⣿⠇⠀⠀    .
⠀⠀⠀⠀⠙⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠀⠀⠀⠀   .
⠀⠀⠀⠀⠀⠀⠀⠙⠻⣿⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀💥
```

### `brockit.py lift`

This is *🚀Brockit!* (Brave Rocket? Brave Rock it? Broke it?): a tool to help
upgrade Brave to a newer Chromium base version. The main goal is to produce
use it to commit the following changes:

 * Update from Chromium [from] to [to].
 * Conflict-resolved patches from Chromium [from] to [to].
 * Update patches from Chromium [from] to [to].
 * Updated strings for Chromium [to].

To start it off, provide a `--to` target version, and a base branch to be used,
either by providing a `--from_ref` argument, or by having an upstream branch to
to your current branch.

```sh
tools/cr/brockit.py lift --to=135.0.7037.1 --from_ref=origin/master
```

Using upstream:

```sh
git branch --set-upstream-to=origin/master
tools/cr/brockit.py lift --to=135.0.7037.1
```

The following steps will take place:

1. A *Update from Chromium [from] to [to]* commit will be created. This commit
   contains changes to `package.json` and to the pinlist timestamp file.
2. `npm run init` will be run with the newer version.
3. For any patches that fail to apply during `init`, there will be another
   attempt to apply them using `--3way`.
4. If any patches still fail to apply, the process will stop. A summary of
   files with conflicts will be provided for resolution.
5. Deleted patches will also cause the  *🚀Brockit!* to stop . The user is
   expected to provide separate commits for deleted patches, explaining the
   reason.
6. Having resolved all conflicts. Restart *🚀Brockit!* with `--continue` and
   other similar arguments you may want to keep (e.g. `--vscode`).
7. *🚀Brockit!* will pick up from where it stopped, possibly running
  `npm run update_patches`, staging all patches, and committing the under
  *Conflict-resolved patches from Chromium [from] to [to].*
8. *Update patches from Chromium [from] to [to]* will be committed.
9. *Updated strings for Chromium [to]* will be committed.

Steps 3-7 may end up being skipped altogether if no failures take place, or in
part if resolution is possible without manual intervention.

The `--restart` flag can be used to start the process from scratch, discarding
everything committed in the last run.

```sh
tools/cr/brockit.py lift --to=135.0.7037.1 --from_ref=origin/master --restart
```

### `brockit.py regen`

Additionally, *🚀Brockit!* can be run with `regen`. This is useful to generate
the "Update patches" and "Updated strings" commits on their own when rebasing
branches, regenerating these files as desired.

```sh
tools/cr/brockit.py update-version-issue
````

### `brockit.py update-version-issue`

The `lift` command supports the use of `--with-github`, which either creates a
new GitHub issue or updates an existing one with the details of the run.
However it is also possible to run this task on standalone as well.

```sh
tools/cr/brockit.py update-version-issue
````

### Infra mode

When running on infra, the `--infra-mode` flag should be provided. This will
suppress all status updates, and rather provide a keep-alive type of feedback
to make sure that the CI doesn't time out.

"""

import argparse
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum, auto
from functools import total_ordering
import itertools
import json
import logging
from pathlib import Path, PurePath
import pickle
import platform
import random
import threading
import re
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.padding import Padding
import subprocess
import sys
import time
from typing import Optional
from typing import NamedTuple

console = Console()

# This file is updated whenever the version number is updated in package.json
PINSLIST_TIMESTAMP_FILE = 'chromium_src/net/tools/transport_security_state_generator/input_file_parsers.cc'
VERSION_UPGRADE_FILE = Path('.version_upgrade')
PACKAGE_FILE = 'package.json'
CHROMIUM_VERSION_FILE = 'chrome/VERSION'

# The path to the brave/ directory.
BRAVE_CORE_PATH = next(brave for brave in PurePath(__file__).parents
                       if brave.name == 'brave')
# The path to chromium's src/ directory.
CHROMIUM_SRC_PATH = BRAVE_CORE_PATH.parent

# Link with the log of changes between two versions.
GOOGLESOURCE_LINK = 'https://chromium.googlesource.com/chromium/src/+log/{from_version}..{to_version}?pretty=fuller&n=10000'

# A decorator to be shown for messages that the user should address before
# continuing.
ACTION_NEEDED_DECORATOR = '[bold yellow](action needed)[/]'

# The text for the body used on a GitHub issue for a version bump.
MINOR_VERSION_BUMP_ISSUE_TEMPLATE = """### Minor Chromium bump

{googlesource_link}

### QA tests

- Check branding items
- Check for version bump

### Minor Chromium bump

- No specific code changes in Brave (only line number changes in patches)
"""

class Terminal:
    """A class that holds the application data and methods.
    """

    def __init__(self):
        # The status object to update with the terminal.
        self.status = None

        # The inital part of the status message, used as a prefix for all
        # updates.
        self.starting_status_message = ''

        # flag indicating if the terminal is running on infra.
        self.infra_mode = False

    def set_infra_mode(self):
        """Sets the terminal to run on infra.
        """
        self.infra_mode = True

    def set_status_object(self, status):
        """Preserves the status object for updates.

    This function is used to preserve the status object for updates, so that
    the status can be updated with the initial status message.
    """
        if self.infra_mode:
            status.stop()
            return

        self.status = status
        self.starting_status_message = status.status

    def run(self, cmd):
        """Runs a command on the terminal.
        """

        # Convert all arguments to strings, to avoid issues with `PurePath`
        # being passed arguments
        cmd = [str(x) for x in cmd]

        def truncate_on_max_length(message):
            # Truncate at the first newline if it exists
            if '\n' in message:
                message = message.split('\n')[0] + '...'
            # Truncate at max_length if the message is still too long
            max_length = console.size.width - len(
                self.starting_status_message) - 10
            if len(message) > max_length:
                message = message[:max_length - 3] + '...'
            return message

        if self.status is not None and not self.infra_mode:
            self.status.update(
                f'[bold green]{self.starting_status_message}[/] [bold cyan]'
                f'({truncate_on_max_length(" ".join(cmd))})[/]')
        logging.debug('λ %s', ' '.join(cmd))

        if self.infra_mode:
            # Start a thread to keep the CI feedback alive while the subprocess
            # is running.
            stop_event = threading.Event()

            def keep_alive_ci_feedback():
                """Keep the CI feedback alive while the subprocess is running.
                """
                feedback = [
                    '(-_-)', '(⊙_⊙)', '(¬_¬)', '(－‸ლ)', '(◎_◎;)', '(⌐■_■)',
                    '(•‿•)', '(≖_≖)'
                ]
                starting_time = time.time()
                while not stop_event.is_set():
                    if time.time() - starting_time < 40:
                        time.sleep(0.05)
                        continue

                    logging.debug(
                        '%s\n        >>>> %s',
                        feedback[random.randint(0,
                                                len(feedback) - 1)],
                        " ".join(cmd))
                    starting_time = time.time()

            # Start subprocess in a thread
            keep_alive_thread = threading.Thread(target=keep_alive_ci_feedback)
            keep_alive_thread.start()

        try:
            # It is necessary to pass `shell=True` on Windows, otherwise the
            # process handle is entirely orphan and can't resolve things like
            # `npm`.
            result = subprocess.run(cmd,
                                    capture_output=True,
                                    text=True,
                                    check=True,
                                    shell=platform.system() == 'Windows')
        except subprocess.CalledProcessError as e:
            logging.debug('❯ %s', e.stderr.strip())
            raise e
        finally:
            if self.infra_mode:
                stop_event.set()
                keep_alive_thread.join()

        return result

    def run_git(self, *cmd) -> str:
        """Runs a git command with the arguments provided.

    This function returns a proper utf8 string in success, otherwise it allows
    the exception thrown by subprocess through.

    e.g:
        self.run_git('add', '-u', '*.patch')
    """
        cmd = ['git'] + list(cmd)
        return self.run(cmd).stdout.strip()

    def log_task(self, message):
        """Logs a task to the console using common decorators
        """
        console.log(f'[bold red]*[/] {message}')

    def run_npm_command(self, *cmd):
        """Runs an npm build command.

      This function will run 'npm run' commands appended by any extra arguments
      are passed into it.

      e.g:
          self.run_npm_command('init')
      """
        cmd = ['npm', 'run'] + list(cmd)
        return self.run(cmd)

terminal = Terminal()


class IncendiaryErrorHandler(RichHandler):
    """ A custom handler that adds emojis to error messages.
    """

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno == logging.ERROR:
            record.msg = f'¯\\_(ツ)_/¯\n🔥🔥 {record.msg}'
        elif record.levelno == logging.DEBUG:
            # Debug messages should be printed as normal logs, otherwise the
            # formatting goes all over the place with the status bar.
            console.log(f'[dim]{record.getMessage()}[/]', _stack_offset=8)
            return

        super().emit(record)


def _get_current_branch_upstream_name():
    """Retrieves the name of the current branch's upstream.
    """
    try:
        return Repository.brave().run_git('rev-parse', '--abbrev-ref',
                                          '--symbolic-full-name',
                                          '@{upstream}')
    except subprocess.CalledProcessError:
        return None

def _load_package_file(branch):
    """Retrieves the json content of package.json for a given revision

  Args:
    branch:
      A branch or hash to load the file from.
  """
    package = Repository.brave().run_git('show', f'{branch}:{PACKAGE_FILE}')
    return json.loads(package)

def _update_pinslist_timestamp():
    """Updates the pinslist timestamp in the input_file_parsers.cc file for the
    version commit.
    """
    try:
        with open(PINSLIST_TIMESTAMP_FILE, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        logging.exception("ERROR: File %s not found. Aborting.",
                          PINSLIST_TIMESTAMP_FILE)
        sys.exit(1)

    pattern = r"# Last updated:.*\nPinsListTimestamp\n[0-9]{10}\n"
    match = re.search(pattern, content, flags=re.DOTALL)
    if not match:
        logging.error(
            'Expected pattern for PinsListTimestamp block not found. '
            'Aborting.')
        sys.exit(1)

    # Update the timestamp
    timestamp = int(datetime.now().timestamp())
    readable_timestamp = datetime.fromtimestamp(timestamp).strftime(
        '%a %b %d %H:%M:%S %Y')
    updated_content = re.sub(
        pattern,
        (f'# Last updated: {readable_timestamp}\nPinsListTimestamp\n'
         f'{timestamp}\n'),
        content,
        flags=re.DOTALL,
    )

    # Write back to the file
    with open(PINSLIST_TIMESTAMP_FILE, "w", encoding="utf-8") as file:
        file.write(updated_content)

    updated = Repository.brave().run_git('diff', PINSLIST_TIMESTAMP_FILE)
    if updated == '':
        raise ValueError('Pinslist timestamp failed to update.')


def _is_gh_cli_logged_in():
    """Checks if the GitHub CLI is logged in.
    """
    try:
        result = terminal.run(['gh', 'auth', 'status']).stdout.strip()
        if 'Logged in to github.com account' in result:
            return True
    except subprocess.CalledProcessError:
        return False

    return False

def _get_apply_patches_list():
    """Retrieves the list of patches to be applied by running 
    `npm run apply_patches`
    """

    try:
        terminal.run_npm_command('apply_patches', '--',
                                 '--print-patch-failures-in-json')
    except subprocess.CalledProcessError as e:
        # This is a regex to match the json output of the patches that failed
        # to apply.
        match = re.search(r'\[\s*{.*?}\s*\]', e.stdout, re.DOTALL)
        if match is None:
            return None
        return json.loads(match.group(0))

    return None


class GitStatus:
    """Runs `git status` and provides a summary.
    """

    def __init__(self):
        self.git_status = Repository.brave().run_git('status', '--short')

        # a list of all deleted files, regardless of their staged status.
        self.deleted = []

        # a list of all modified files, regardless of their staged status.
        self.modified = []

        # a list of all untracked files.
        self.untracked = []

        for line in self.git_status.splitlines():
            [status, path] = line.lstrip().split(' ', 1)
            if status == 'D':
                self.deleted.append(path)
            elif status == 'M':
                self.modified.append(path)
            elif status == '??':
                self.untracked.append(path)

    def has_deleted_files(self):
        return len(self.deleted) > 0

    def has_deleted_patch_files(self):
        return any(path.endswith('.patch') for path in self.deleted)

    def has_untracked_patch_files(self):
        return any(path.endswith('.patch') for path in self.untracked)


@dataclass(frozen=True)
class Repository:
    """Repository data class to hold the repository path.

    This class provides helpers around the use of repository paths, such as
    relative paths to and from the repository, and repository specific git
    operations.
    """

    # The repository path. This path is extracted from the subdirectory section
    # of a patch file, with chromium/src being ''.
    # e.g. "third_party/search_engines_data/resources"
    path: PurePath

    @classmethod
    def chromium(cls) -> "Repository":
        """Returns the chromium/src repository.
        """
        return cls(PurePath(CHROMIUM_SRC_PATH))

    @classmethod
    def brave(cls) -> "Repository":
        """Returns the brave/ repository.
        """
        return cls(BRAVE_CORE_PATH)

    @property
    def is_chromium(self) -> bool:
        """If this repo is chromium/src.
        """
        return self.path == CHROMIUM_SRC_PATH

    @property
    def is_brave(self) -> bool:
        """If this repo is brave/.
        """
        return self.path == BRAVE_CORE_PATH

    def to_brave(self) -> PurePath:
        """ Returns the path from the repository to brave/.
        """
        if self.is_chromium:
            return BRAVE_CORE_PATH.relative_to(CHROMIUM_SRC_PATH)
        return PurePath(
            len(self.path.relative_to(CHROMIUM_SRC_PATH).parts) *
            '../') / BRAVE_CORE_PATH.relative_to(CHROMIUM_SRC_PATH)

    def from_brave(self) -> PurePath:
        """ Returns the path from brave/ to the repository.
        """
        return PurePath('..') / self.path.relative_to(CHROMIUM_SRC_PATH)

    def run_git(self, *cmd) -> str:
        """Runs a git command on the repository.
        """
        if self.is_brave:
            return terminal.run_git(*cmd)

        return terminal.run_git('-C', self.from_brave(), *cmd)

    def unstage_all_changes(self):
        """Unstages all changes in the repository.
        """
        self.run_git('reset', 'HEAD')

    def has_staged_changed(self):
        return self.run_git('diff', '--cached', '--stat') != ''

    def get_commit_short_description(self, commit: str = 'HEAD') -> str:
        """Gets the short description of a commit.

        This is just the actual first line of the commit message.
        """
        return self.run_git('log', '-1', '--pretty=%s', commit)

    def git_commit(self, message):
        """Commits the current staged changes.

        This function also prints the commit hash/message to the user.
        Args:
        message:
            The message to be used for the commit.
        """
        if self.has_staged_changed() is False:
            # Nothing to commit
            return

        self.run_git('commit', '-m', message)
        commit = self.run_git('log', '-1', '--pretty=oneline',
                              '--abbrev-commit')
        terminal.log_task(f'[bold]✔️ [/] [italic]{commit}')

    def is_valid_git_reference(self, reference) -> bool:
        """Checks if a name is a valid git branch name or hash.
        """
        try:
            self.run_git('rev-parse', '--verify', reference)
            return True
        except subprocess.CalledProcessError:
            return False

    def last_changed(self,
                     file: str,
                     from_commit: Optional[str] = None) -> str:
        """Gets the last commit for a file.
        """
        args = ['log', '--pretty=%h', '-1']
        if from_commit:
            args.append(from_commit)
        args.append(file)
        return self.run_git(*args)

@dataclass(frozen=True)
class Patchfile:
    """Patchfile data class to hold the patchfile path.

    This class provides methods to manage the information regarding individual
    patches, such as the source file name, the repository, and the status of the
    patch application, etc.
    """

    # A patch's path and file name, from `patchPath`.
    # e.g. "patchPath":"patches/build-android-gyp-dex.py.patch"
    path: PurePath

    # This field holds the name of the source file as provided by
    # `update_patches`, which is not a primary source.
    # e.g. "path":"build/android/gyp/dex.py"
    provided_source: Optional[str] = field(default=None)

    # This field holds the most reliable resolution to the source file name,
    # as its value is assigned from a git operation.
    source_from_git: Optional[str] = field(default=None)

    # The repository the patch file is targeting to patch.
    repository: Repository = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'repository',
                           self.get_repository_from_patch_name())

    def get_repository_from_patch_name(self) -> Repository:
        """Gets the repository for the patch file.
        """
        if self.path.suffix != '.patch':
            raise ValueError(
                f'Patch file name should end with `.patch`. {self.path}')
        if self.path.is_absolute() or len(
                self.path.parents
        ) < 2 or self.path.parents[-2].stem != "patches":
            raise ValueError(
                f'Patch file name should start with `patches/`. {self.path}')

        # Drops `patches/` at the beginning and the filename at the end.
        return Repository(CHROMIUM_SRC_PATH.joinpath(*self.path.parts[1:-1]))

    class ApplyStatus(Enum):
        """The result of applying the patch.
        """

        # The patch was applied successfully.
        CLEAN = auto()

        # The patch was applied with conflicts.
        CONFLICT = auto()

        # The patch could not be applied because the source file was deleted.
        DELETED = auto()

        # The patch failed as broken.
        BROKEN = auto()

    class ApplyResult(NamedTuple):
        """The result of applying the patch.
        """
        # The status of the patch operation
        status: "ApplyStatus"

        # A copy of the patch file data, with updated information.
        patch: Optional["Patchfile"]

    @dataclass
    class SourceStatus:
        """The status of the source file in a given commit.
        """

        # A code for the status of the source file. (e.g 'R', 'M', 'D')
        status: str

        # The commit details for this source file status.
        commit_details: str

        # The name the source may have been renamed to.
        renamed_to: Optional[str] = None

    def source_name_from_patch_naming(self) -> str:
        """Source file name according to the patch file name.

        This function uses the patch file name to deduce the source file name.
        This works in general, but it is not the most reliable method to
        determine the source file name, and it should be used only in cases
        where git, and `apply_patches` cannot provide the source file name.

        e.g. "patches/build-android-gyp-dex.py.patch" ->
             "brave/build/android/gyp/dex.py"
        """
        return self.path.name[:-len(".patch")].replace('-', '/')

    def source(self) -> PurePath:
        """The source file name for the patch file.

        Tries to use the most reliable source file name, going from git, to the
        one provide by `apply_patches`, to finally deducing from the name.
        """
        if self.source_from_git is not None:
            return self.source_from_git
        if self.provided_source is not None:
            return self.provided_source
        return self.source_name_from_patch_naming()

    def source_from_brave(self) -> PurePath:
        """The source file path relative to the `brave/` directory.
        """
        return f'{self.repository.from_brave() / self.source()}'

    def path_from_repo(self) -> PurePath:
        """The patch path relative to the repository source belongs.
        """
        return f'{self.repository.to_brave() / self.path}'

    def apply(self) -> ApplyResult:
        """Applies the patch file with `git apply --3way`.

        This function applies the patch file with `git apply --3way` to the
        repository, and it returns the status of the operation.

        Args:
            repo:
                The repository to apply the patch to. If not provided, the
                repository is deduced from the patch file name.

        Returns:
            The result of the patch application, and an updated patch instance
            with the source file name, if any is provided by git.
        """

        try:
            self.repository.run_git('apply', '--3way', '--ignore-space-change',
                                    '--ignore-whitespace',
                                    self.path_from_repo())
            return self.ApplyResult(self.ApplyStatus.CLEAN, None)
        except subprocess.CalledProcessError as e:
            # If the process fails, we need to collect the files that failed to
            # apply for manual conflict resolution.
            if 'with conflicts' in e.stderr:
                # Output in this case should look like:
                #   Applied patch to 'build/android/gyp/dex.py' with conflicts.
                #   U build/android/gyp/dex.py
                # We get the file name from the last line.
                return self.ApplyResult(
                    self.ApplyStatus.CONFLICT,
                    replace(self,
                            source_from_git=e.stderr.strip().splitlines()
                            [-1].split()[-1]))
            if e.stderr.startswith('error:'):
                [_, reason] = e.stderr.strip().split(': ', 1)

                if 'does not exist in index' in reason:
                    # This type of detection could occur in certain cases when
                    # `npm run init` or `sync` were not run for the working
                    # branch. It may be useful to warn.
                    #
                    # It is also of notice that this error can also occur when
                    # `apply` is run twice for the same patch with conflicts.
                    logging.warning(
                        'Patch with missing file detected during --3way apply,'
                        ' which may indicate a bad sync state before starting '
                        'to upgrade. %s', self.path)
                    return self.ApplyResult(
                        self.ApplyStatus.DELETED,
                        replace(self, source_from_git=reason.split(': ',
                                                                   2)[0]))
                if ('No such file or directory' in reason
                        and self.path in reason):
                    # This should never occur as it indicates that the patch
                    # file itself is missing, which is sign something is wrong
                    # with path resolution.
                    raise e

                # All other errors are considered broken patches.
                if 'patch with only garbage' not in reason:
                    # Not clear if we could have other reasons for broken
                    # patches, but it is better to flag it to keep an eye out
                    # for it.
                    logging.warning(
                        'Patch being flagged as broken, but with unexpected '
                        'reason: %s %s', self.path, reason)

                return self.ApplyResult(self.ApplyStatus.BROKEN, None)

        raise NotImplementedError()

    def fetch_source_from_git(self) -> "Patchfile":
        """Gets the source file name from git.

        This function uses git to get the source file name for the patch file,
        but only if such name has not been retrieved yet from git.

        Returns:
            A patch instance with the source file name from git.
        """

        if self.source_from_git is not None:
            return self

        # The command below has an output similar to:
        # 8	0	base/some_file.cc
        return replace(self,
                       source_from_git=self.repository.run_git(
                           'apply', '--numstat', '-z',
                           self.path_from_repo()).strip().split()[2][:-1])

    def get_last_commit_for_source(self) -> str:
        """Gets the last commit where the source file was mentioned.

        This function uses git to get the last commit where the source file was
        mentioned, which can be used to check details of when a source was
        deleted, or renamed.

        Returns:
            The commit hash with the last mention for the source.
        """
        return self.repository.run_git('log', '--full-history', '--pretty=%h',
                                       '-1', '--', self.source())

    def get_source_removal_status(self, commit: str) -> SourceStatus:
        """Gets the status of the source file in a given commit.

        This function retrieves the details of the source file in a given
        commit. This is useful to check if a file has been deleted, or
        renamed.

        Args:
            commit:
                The commit hash to check the source file status.

        Returns:
            The status of the source file in the commit, which also includes
            the commit description.
        """

        # Not very sure why, but by passing `--no-commit-id` the
        # output looks something like this:
        # M       chrome/VERSION
        # commit 17bb6c858e818e81744de42ed292b7060bc341e5
        # Author: Chrome Release Bot (LUCI)
        # Date:   Wed Feb 26 10:17:33 2025 -0800
        #
        #     Incrementing VERSION to 134.0.6998.45
        #
        #     Change-Id: I6e995e1d7aed40e553d3f51e98fb773cd75
        #
        # So the output is read and split from the moment a line starts with
        # `commit`.
        change = self.repository.run_git('show', '--name-status',
                                         '--no-commit-id', commit)
        [all_status, commit_details] = re.split(r'(?=^commit\s)',
                                                change,
                                                flags=re.MULTILINE)

        # let's look for the line about the source we care about.
        status_line = next(
            (s for s in all_status.splitlines() if str(self.source()) in s),
            None)
        status_code = status_line[0]

        if status_code == 'D':
            return self.SourceStatus(status=status_code,
                                     commit_details=commit_details)
        if status_code == 'R':
            # For renames the output looks something like:
            # R100       base/some_file.cc       base/renamed_to_file.cc
            return self.SourceStatus(status=status_code,
                                     commit_details=commit_details,
                                     renamed_to=status_line.split()[-1])

        # This could change in the future, but for now it only makes sense to
        # use this function for deleted or renamed files.
        raise NotImplementedError(f'unreachable: {status_line}')


@dataclass(frozen=True)
class PatchfilesContinuation:
    """A class to hold the continuation data for patches.
    """

    # A dictionary of all patches with attempted `--3way`, grouped by
    # repository.
    patch_files: dict[Repository, Patchfile] = field(default_factory=dict)

    # A list of patches that cannot be applied due to their source file being
    # deleted.
    patches_to_deleted_files: list[Patchfile] = field(default_factory=list)

    # A list of files that require manual conflict resolution before continuing.
    files_with_conflicts: list[str] = field(default_factory=list)

    # A list of patches that fail entirely when running apply with `--3way`.
    broken_patches: list[Patchfile] = field(default_factory=list)


@total_ordering
@dataclass(frozen=True)
class Version:
    """A class to hold the version information.
    """

    # The version data in the format of 'MAJOR.MINOR.BUILD.PATCH'
    value: str

    def __post_init__(self):
        if len(self.parts) != 4:
            raise ValueError(
                'Version required format: MAJOR.MINOR.BUILD.PATCH. '
                f'version={self.value}')

    def __str__(self):
        return self.value

    @property
    def parts(self) -> list[int]:
        """The version parts as integers.
        """
        return tuple(map(int, self.value.split('.')))

    @property
    def major(self) -> int:
        """The major version part.
        """
        return self.parts[0]

    @classmethod
    def from_git(cls, branch: str) -> "Version":
        """Retrieves the version from the git repository.
        """
        return cls(
            _load_package_file(branch).get('config').get('projects').get(
                'chrome').get('tag'))

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.parts == other.parts

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.parts < other.parts

    @classmethod
    def from_upstream(cls) -> Optional["Version"]:
        """Retrieves the version from the upstream branch.

        Returns:
            The version from the upstream branch, or None no upstream branch is
            set in the current branch.
        """
        upstream_branch = _get_current_branch_upstream_name()
        if upstream_branch is None:
            return None

        return Version.from_git(upstream_branch)

    @classmethod
    def from_previous(cls) -> "Version":
        """Retrieves the previous version from the last bump.

        This function looks for what was in the package.json file before the
        last upgraded in the current branch.
        """
        starting_version = Version.from_git('HEAD')
        base_version = starting_version
        last_changed = Repository.brave().last_changed(PACKAGE_FILE)
        last_changed = Repository.brave().last_changed(PACKAGE_FILE)
        while True:
            base_version = Version.from_git(f'{last_changed}~1')
            if base_version != starting_version:
                break
            # Prefer to look for the PACKAGE_FILE here, because this has to
            # resolve even when the upgrade was done manually, so don't assume
            # the presence of pinslist timestamp changes.
            last_changed = Repository.brave().last_changed(
                PACKAGE_FILE, f'{last_changed}~1')
        return base_version

    def get_googlesource_diff_link(self, from_version: "Version") -> str:
        """Generates a link to the diff of the upgrade.
        """
        return GOOGLESOURCE_LINK.format(from_version=from_version,
                                        to_version=self)


@dataclass(frozen=True)
class ContinuationFile:
    """A class to hold the continuation data for the upgrade process.
    """

    # The target version that brockit is aiming to upgrade brave to.
    target_version: Version

    # The version that was in the branch when the upgrade started (which can be
    # different from the base version).
    working_version: Version

    # The base version for the upgrade process. This is saved as a reference
    # like @previous cannot be relied on once we committed a change, moving the
    # previous branch ahead.
    base_version: Version

    # The continuation data for the patches.
    patches: Optional[PatchfilesContinuation] = field(default=None)

    @staticmethod
    def load(target_version: Version,
             check: bool = True) -> Optional["ContinuationFile"]:
        """Loads the continuation file.
        """
        if VERSION_UPGRADE_FILE.exists() is False:
            if check:
                raise FileNotFoundError(
                    f'File {VERSION_UPGRADE_FILE} does not exist')
            return None

        with open(VERSION_UPGRADE_FILE, 'rb') as file:
            continuation = pickle.load(file)

        if continuation.target_version != target_version:
            if not check:
                return None

            # This validation is in place for something that shouldn't happen.
            # If this is being hit, it means some wrong continuation file is in
            # the tree, and the process should be started all over.
            raise TypeError(
                F'Target version in {VERSION_UPGRADE_FILE} does not match the '
                f'target version. expected: {target_version} '
                f'vs {continuation.target_version}')

        return continuation

    def save(self):
        """Saves the continuation file.
        """
        with open(VERSION_UPGRADE_FILE, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def clear():
        logging.debug('Clearing the continuation file.')
        try:
            Path(VERSION_UPGRADE_FILE).unlink()
        except FileNotFoundError:
            pass

class PatchFailureResolver:
    """Assist patch-failure resolutions, applying patches, reseting patches.

    This class provides methods to assist with patch failures, including:
    - Applying patches with `--3way`.
    - Resetting patches that have been applied.
    - Reporting on deleted/renamed source files.
    - Reporting on broken patches.

    This class uses a continuation file to allow for multisession patch
    resolution.
  """

    def __init__(self, continuation: Optional[ContinuationFile] = None):
        # A dictionary that holds a list for all patch files affected, by
        # repository.
        self.patch_files = {}

        # This is a flat of list of patches that cannot be applied due to their
        # source file being deleted.
        self.patches_to_deleted_files = []

        # A list of files that require manual conflict resolution before
        # continuing.
        self.files_with_conflicts = []

        # These are patches that fail entirely when running apply with `--3way`.
        self.broken_patches = []

        if continuation is not None:
            # Load it from the continuation file.
            self.patch_files = continuation.patches.patch_files
            self.patches_to_deleted_files = (
                continuation.patches.patches_to_deleted_files)
            self.files_with_conflicts = (
                continuation.patches.files_with_conflicts)
            self.broken_patches = continuation.patches.broken_patches

    def apply_patches_3way(self,
                           target_version: Version,
                           launch_vscode: bool = False):
        """Applies patches that have failed using the --3way option to allow for
        manual conflict resolution.

        This method will apply the patches and reset the state of applied
        patches. Additionally, it will also produce a list of the files that
        are waiting for conflict resolution.

        A list of the patches applied will be produced as well.
        """
        if len(self.patch_files) > 0:
            raise NotImplementedError(
                'unreachable: 3way apply should happen only once.')

        # the raw list of patches that failed to apply.
        patch_failures = _get_apply_patches_list()
        if patch_failures is None:
            raise ValueError(
                'Apply patches failed to provide a list of patches.')

        for entry in patch_failures:
            patch = Patchfile(path=PurePath(entry['patchPath']),
                              provided_source=entry.get('path'))

            if entry['reason'] == 'SRC_REMOVED':
                # Skip patches that can't apply as the source is gone.
                self.patches_to_deleted_files.append(patch)
                continue

            # Grouping patch files by their repositories, so to allow us to
            # iterate through them, applying them in their repo paths.
            self.patch_files.setdefault(patch.repository, []).append(patch)

        if len(self.patch_files):
            terminal.log_task(
                '[bold]Reapplying patch files with --3way:\n[/]%s' %
                '\n'.join(f'    * {file}' for file in [
                    patch.path for patch_list in self.patch_files.values()
                    for patch in patch_list
                ]))

        vscode_args = ['code']
        for repo, patches in self.patch_files.items():
            for patch in patches:
                apply_result = patch.apply()
                if apply_result.status == Patchfile.ApplyStatus.CONFLICT:
                    source = patch.source_from_brave()
                    self.files_with_conflicts.append(source)
                elif apply_result.status == Patchfile.ApplyStatus.BROKEN:
                    self.broken_patches.append(patch)
                elif apply_result.status == Patchfile.ApplyStatus.DELETED:
                    self.patches_to_deleted_files.append(patch)

        for repo, patches in self.patch_files.items():
            # Resetting any staged states from apply patches as that can cause
            # issues when generating patches.
            repo.unstage_all_changes()

        if len(self.patches_to_deleted_files) > 0:
            # The goal in this this section is print a report for listing every
            # patch that cannot apply anymore because the source file is gone,
            # fetching from git the commit and the reason why exactly the file
            # is not there anymore (e.g. renamed, deleted).

            terminal.log_task('[bold]Files that cannot be patched anymore '
                              f'{ACTION_NEEDED_DECORATOR}:[/]')

            # This set will hold the information about the deleted patches
            # in a way that they can be grouped around the chang that caused
            # their removal.
            deletion_report = {}

            for patch in self.patches_to_deleted_files:
                # Make sure we have an correct file source for the patch.
                patch = patch.fetch_source_from_git()
                # Finding the culptrit commit hash.
                commit = patch.get_last_commit_for_source()
                deletion_report.setdefault(
                    commit,
                    {})[patch] = patch.get_source_removal_status(commit)

            for commit, patches in deletion_report.items():
                for patch, status in patches.items():
                    if status.status == 'D':
                        console.log(
                            Padding(f'✘ {patch.source()} [red bold](deleted)',
                                    (0, 4)))
                        vscode_args.append(patch.path)
                    elif status.status == 'R':
                        renamed_to = patch.repository.from_brave(
                        ) / status.renamed_to
                        console.log(
                            Padding(
                                f'✘ {patch.source_from_brave()}\n    '
                                f'([yellow bold]renamed to[/] {renamed_to})',
                                (0, 4)))
                        vscode_args += [patch.path, renamed_to]

            # Printing the commmit message for the grouped changes.
            console.log(
                Padding(f'{next(iter(patches.items()))[1].commit_details}\n',
                        (0, 8),
                        style="dim"))

        if len(self.broken_patches) > 0:
            terminal.log_task(
                '[bold]Broken patches that fail to apply entirely '
                f'{ACTION_NEEDED_DECORATOR}:[/]')

            for patch in self.broken_patches:
                source = patch.source_from_brave()
                console.log(Padding(f'✘ {patch.path} ➜ {source}', (0, 4)))
                vscode_args += [patch.path, source]

        if len(self.files_with_conflicts) > 0:
            vscode_args += self.files_with_conflicts
            file_list = '\n'.join(f'    ✘ {file}'
                                  for file in self.files_with_conflicts)
            terminal.log_task(f'[bold]Manually resolve conflicts for '
                              f'{ACTION_NEEDED_DECORATOR}:[/]\n{file_list}')

        # The continuation file is updated at the end of the process, in case
        # the process has to be continued later.
        replace(ContinuationFile.load(target_version=target_version),
                patches=PatchfilesContinuation(
                    patch_files=self.patch_files,
                    patches_to_deleted_files=self.patches_to_deleted_files,
                    files_with_conflicts=self.files_with_conflicts,
                    broken_patches=self.broken_patches)).save()

        if launch_vscode and len(vscode_args) > 1:
            terminal.run(vscode_args)

    def requires_conflict_resolution(self):
        return len(self.files_with_conflicts) > 0 or len(
            self.patches_to_deleted_files) > 0 or len(self.broken_patches) > 0

    def stage_all_patches(self, ignore_deleted_files=False):
        """Stages all patches that were applied, so they can be committed as
        conflict-resolved patches.

        Args:
            ignore_deleted_files:
                If set to True, deleted files will be ignored, and not staged.
        """
        for _, patches in self.patch_files.items():
            for patch in patches:
                if (ignore_deleted_files is True
                        and Path(patch.path).exists() is False):
                    # Skip deleted files.
                    continue

                Repository.brave().run_git('add', patch.path)

def _read_chromium_version_file():
    """Retrieves the Chromium version from the VERSION file.

    This function reads directly from git, as VERSION gets patched during
    `apply_patches`.
    """
    version_parts = {}
    file = Repository.chromium().run_git('show',
                                         f'HEAD:{CHROMIUM_VERSION_FILE}')
    for line in file.splitlines():
        key, value = line.strip().split('=')
        version_parts[key] = value
    return Version('{MAJOR}.{MINOR}.{BUILD}.{PATCH}'.format(**version_parts))


class Task:
    """ Base class for all tasks in brockit.

    This class provides a common interface for other tasks to build upon. It
    provides a run method that will execute the task, and a status_message
    method that will return a string to be displayed while the task is running.
    """

    def run(self, *cmd) -> bool:
        """Runs the task with a status message.

        This function will run the task inside the scope of a status message.

        Args:
            an open set of argument to be passed along to the derived class's
            execute method.

        Returns:
            The result `execute()`. True if sucessful, False otherwise.
        """
        console.log('[italic]🚀 Brockit!')
        with console.status(self.status_message()) as status:
            terminal.set_status_object(status)
            result = self.execute(*cmd)

            if result:
                console.log('[bold]💥 Done!')

        return result

    def status_message(self) -> str:
        """Returns a status message for the task.

        This function has to be implemented by the derived class.
        """
        raise NotImplementedError

    def execute(self) -> bool:
        """Executes the task.

        This function has to be implemented by the derived class.
        """
        raise NotImplementedError


class Versioned(Task):
    """ Base class for all versioned tasks.

    Versioned tasks are tasks that have the concept of a base version and a
    target version.
    """

    def __init__(self,
                 base_version: Version,
                 target_version: Optional[Version] = None):
        # The version in `package.json` found in that upstream branch.
        self.base_version = base_version

        # The target of a given upgrade.
        self.target_version = target_version
        if self.target_version is None:
            # When not provided we default for whatever is in the current
            # branch because that's is possibly what the target version is for
            # maintainance tasks.
            self.target_version = Version.from_git('HEAD')

        if self.target_version <= self.base_version:
            logging.error(
                'Target version is not higher than base version: '
                'target=%s, base=%s', self.target_version, self.base_version)
            sys.exit(1)

    def execute(self) -> bool:
        raise NotImplementedError

    def _save_updated_patches(self):
        """Creates the updated patches change

    This function creates the third commit in the order of the update, saving
    all patches that might have been changed or deleted. Untracked patches are
    excluded from addition at this stage.
    """
        Repository.brave().run_git('add', '-u', '*.patch')

        Repository.brave().git_commit(
            f'Update patches from Chromium {self.base_version} '
            f'to Chromium {self.target_version}.')

    def _save_rebased_l10n(self):
        """Creates string rebase change

    This function stages, and commits, all changed, updated, or deleted files
    resulting from running npm run chromium_rebase_l10n.
    """
        Repository.brave().run_git('add', '*.grd', '*.grdp', '*.xtb')
        Repository.brave().git_commit(
            f'Updated strings for Chromium {self.target_version}.')


class Regen(Versioned):
    """Regenerates patches and strings for the current branch.

    This task is used for cases where the user wants to regenerate patches and
    strings. The purpose is to produce `Update patches` and `Updated strings`
    where approrpriate.
    """

    def status_message(self):
        return "Updating patches and strings..."

    def execute(self) -> bool:
        terminal.log_task(
            f'Processing changes for Chromium {self.base_version} '
            f'to Chromium {self.target_version}.')
        terminal.run_npm_command('init')
        terminal.run_npm_command('update_patches')
        self._save_updated_patches()
        terminal.run_npm_command('chromium_rebase_l10n')
        self._save_rebased_l10n()
        return True


class GitHubIssue(Versioned):
    """Creates a GitHub issue for the upgrade.

    This class offers ways to create or update the github issue for the
    upgrade. Also, as this is its own task, it can be called on its own for
    maintainance purposes.
    """

    def status_message(self):
        return "Creating/Updating GitHub issue for upgrade..."

    def create_or_updade_version_issue(self):
        """Creates a github issue for the upgrade.

        This function creates/updates the upgrade github issue.
        """

        title = 'Upgrade from Chromium {previous} to Chromium {to}'
        if self.target_version.major > self.base_version.major:
            # For major updates, the issue description doesn't have a precise
            # version number.
            title = title.format(previous=str(self.base_version.major),
                                 to=str(self.target_version.major))
        else:
            title = title.format(previous=str(self.base_version),
                                 to=str(self.target_version))

        link = self.target_version.get_googlesource_diff_link(
            from_version=str(self.base_version))

        results = json.loads(
            terminal.run([
                'gh', 'issue', 'list', '--repo', 'brave/brave-browser',
                '--search', title, '--state', 'open', '--json',
                'number,title,url,body'
            ]).stdout.strip())
        issue = next((entry for entry in results if entry['title'] == title),
                     None)
        if issue is not None:
            pattern = r"https://chromium\.googlesource\.com/chromium/src/\+log/[^\s]+"
            body = re.sub(pattern, link, issue['body'])
            if body == issue['body']:
                console.log(
                    f'A Github issue with the title "{title}" is already '
                    f'created and up-to-date. {str(issue["url"])}')
            else:
                terminal.run([
                    'gh', 'issue', 'edit',
                    str(issue['number']), '--repo', 'brave/brave-browser',
                    '--body', f'{body}'
                ])
                terminal.log_task(f'GitHub issue udpated {str(issue["url"])}.')
            return

        body = MINOR_VERSION_BUMP_ISSUE_TEMPLATE.format(googlesource_link=link)
        issue_url = terminal.run([
            'gh', 'issue', 'create', '--repo', 'brave/brave-browser',
            '--title', title, '--body', f'{body}', '--label',
            '"Chromium/upgrade minor"', '--label', '"OS/Android"', '--label',
            '"OS/Desktop"', '--label', '"QA/Test-Plan-Specified"', '--label',
            '"QA/Yes"', '--label', '"release-notes/include"', '--assignee',
            'emerick', '--assignee', 'mkarolin', '--assignee',
            'cdesouza-chromium'
        ]).stdout.strip()
        terminal.log_task(f'GitHub Issue created for this bump: {issue_url}')

    def execute(self) -> bool:
        if _is_gh_cli_logged_in() is False:
            logging.error('GitHub CLI is not logged in.')
            return False

        self.create_or_updade_version_issue()
        return True


class ReUpgrade(Task):
    """Restarts the upgrade process.

    This class is called when `--restart` is provided and it is useful when one
    wants to restart fresh. It will reset the repository to where it was before
    the update started.
    """

    def __init__(self, target_version: Version):
        # The target version passed to --to, which is used to make sure the
        # restart is being done in the right place.
        self.target_version = target_version

    def status_message(self):
        return "Restarting the upgrade process..."

    def execute(self) -> bool:
        """Restarts the upgrade process.

        This function will reset the repository to the state it was before the
        upgrade started. It will also clear the continuation file.
        """
        working_version = Version.from_git('HEAD')
        if self.target_version != working_version:
            logging.error(
                'Running with `--restart` but the target version does not '
                'match the current version. %s vs %s', self.target_version,
                working_version)
            return False

        starting_change = Repository.brave().last_changed(
            PINSLIST_TIMESTAMP_FILE)
        commit_message = Repository.brave().get_commit_short_description(
            starting_change)
        if not commit_message.startswith(
                'Update from Chromium ') or not commit_message.endswith(
                    f' to Chromium {self.target_version}.'):
            logging.error(
                'Running with `--restart` but the last change does match the '
                'arguments provide. %s %s', starting_change, commit_message)
            return False

        console.log('Discarding the following changes:')
        console.log(
            Padding(
                '[dim]%s' % Repository.brave().run_git(
                    'log', '--pretty=%h %s', f'HEAD...{starting_change}~1'),
                (0, 4)))

        ContinuationFile.clear()
        Repository.brave().run_git('reset', '--hard', f'{starting_change}~1')
        return True

class Upgrade(Versioned):
    """The upgrade process, holding the data related to the upgrade.

  This class produces an object that is reponsible for keeping track of the
  upgrade process step-by-step. It acquires all the common data necessary for
  its completion.
  """

    def __init__(self,
                 target_version: Version,
                 is_continuation: bool,
                 base_version: Optional[Version] = None):
        if ((base_version is None and is_continuation is False)
                or (base_version is not None and is_continuation is True)):
            # either it is a new upgrade, and a base version is provided, or it
            # is a continuation and no base version is provided as it gets read
            # from disk.
            raise NotImplementedError()

        # Indicates that the upgrade is a continuation from a previous run.
        self.is_continuation = is_continuation

        # The last version the branch was in, that the update is being started
        # from
        self.working_version = None
        if self.is_continuation:
            version_on_head = Version.from_git('HEAD')
            if target_version != version_on_head:
                logging.error(
                    'Running with `--continue` on a branch with a different '
                    'version what the target should be. %s vs %s',
                    target_version, version_on_head)
                sys.exit(1)

            # Loads the working version from the continuation file, because the
            # current branch has already updated the working version to the
            # target version.
            try:
                continuation = ContinuationFile.load(
                    target_version=target_version)
            except FileNotFoundError:
                logging.error(
                    '%s continuation file does not exist. (Are you sure you '
                    'meant to pass [bold cyan]--continue[/]?)',
                    VERSION_UPGRADE_FILE)
                sys.exit(1)
            self.working_version = continuation.working_version
            base_version = continuation.base_version
        else:
            self.working_version = Version.from_git('HEAD')

        # The version currently set in the VERSION file.
        self.chromium_src_version = _read_chromium_version_file()

        super().__init__(base_version, target_version)

    def status_message(self):
        return "Upgrading Chromium base version"

    def _update_package_version(self):
        """Creates the change upgrading the Chromium version

    This is for the creation of the first commit, which means updating
    package.json to the target version provided, and commiting the change to
    the repo
    """
        package = _load_package_file('HEAD')
        package['config']['projects']['chrome']['tag'] = str(
            self.target_version)
        with open(PACKAGE_FILE, "w") as package_file:
            json.dump(package, package_file, indent=2)

        Repository.brave().run_git('add', PACKAGE_FILE)

        # Pinlist timestamp update occurs with the package version update.
        _update_pinslist_timestamp()
        Repository.brave().run_git('add', PINSLIST_TIMESTAMP_FILE)
        Repository.brave().git_commit(
            f'Update from Chromium {self.base_version} '
            f'to Chromium {self.target_version}.')

    def _save_conflict_resolved_patches(self):
        Repository.brave().git_commit(
            f'Conflict-resolved patches from Chromium {self.base_version} to '
            f'Chromium {self.target_version}.')

    def _run_update_patches_with_no_deletions(self):
        """Runs update_patches and returns if any deleted patches are found.

        This function is usually preferred, as it checks if any patches are
        deleted after running update_patches. Deleted patches should be
        committed manually with a history of why the patching is not required
        anymore.

        return:
          Returns True if no deleted patches are found, and False otherwise.
        """
        terminal.run_npm_command('update_patches')

        status = GitStatus()
        if status.has_deleted_patch_files() is True:
            logging.error(
                'Deleted patches detected. These should be committed as their '
                'own changes:\n%s' % '\n'.join(status.deleted))
            return False
        if status.has_untracked_patch_files() is True:
            logging.error(
                'Untracked patch files detected. These should be committed as '
                'their own changes:\n%s' % '\n'.join(status.untracked))
            return False

        return True

    def _get_googlesource_history_link(self, from_version):
        """Generates a link to the review history of the upgrade.

    This function generates a link to the review history of changes between the
    base version and the target version, for the current run.
        """

        return f'https://chromium.googlesource.com/chromium/src/+log/{from_version}..{self.target_version}?pretty=fuller&n=10000'

    def _continue(self, no_conflict_continuation: bool) -> bool:
        """Continues the upgrade process.

    This function is responsible for continuing the upgrade process. It will
    pick up from where the process left the last time.

    This function handles resumption in a way that the user may have to call
    brockit with `--continue` multiple times, which will result in this
    function being called every time.

    Files that are staged are considered as being meant for the
    `conflict-resolved` change. Deleted files will cause this function to bail
    out, so the user provide a commit message for the deletion.

    Args:
        no_conflict_continuation:
            Indicates that a continuation does not produce a conflict-resolved
            change.
        """
        if no_conflict_continuation is not True:
            # There's no need to try to create a `conflict-resolved` commit if
            # all changes have already been committed during the run's break.
            resolver = PatchFailureResolver(
                ContinuationFile.load(self.target_version))

            if resolver.requires_conflict_resolution() is True:
                if self._run_update_patches_with_no_deletions() is not True:
                    return False

            resolver.stage_all_patches(ignore_deleted_files=True)

            if Repository.brave().has_staged_changed() is False:
                logging.error(
                    'Nothing has been staged to commit conflict-resolved '
                    'patches.')
                return False

            self._save_conflict_resolved_patches()

        self._save_updated_patches()
        # Run init again to make sure nothing is missing after updating
        # patches.
        terminal.run_npm_command('init')

        terminal.run_npm_command('chromium_rebase_l10n')
        self._save_rebased_l10n()

        # With the continuation finished there's no need to keep the
        # continuation file around.
        ContinuationFile.clear()

        return True

    def _start(self, launch_vscode: bool) -> bool:
        """Starts the upgrade process.

    This function is responsible for starting the upgrade process. It will
    update the package version, run `npm run init`, and then run
    `npm run update_patches`. If any patches fail to apply, it will run
    `npm run apply_patches_3way` to allow for manual conflict resolution.

    For cases where no conflict resolution is required, the process will
    will continue, concluding the whole four steps of the upgrade process.

    Args:
        launch_vscode:
            Indicates if the user wants to launch vscode with the patches that
            require manual conflict resolution.

    Return:
        Returns True if the process was successful, and False otherwise.
        """
        if (self.working_version != self.chromium_src_version
                and self.target_version != self.chromium_src_version):
            logging.warning(
                'Chrommium seems to be synced to a version entirely '
                'unrelated. Brave %s ➜ Chromium %s', self.working_version,
                self.chromium_src_version)
        elif self.working_version != self.chromium_src_version:
            logging.warning(
                'Chromium is checked out with the target version. '
                'Brave %s ➜ Chromium %s', self.working_version,
                self.chromium_src_version)

        if self.working_version != self.base_version:
            terminal.log_task('Changes for this bump: %s' %
                              self.target_version.get_googlesource_diff_link(
                                  self.working_version))
        terminal.log_task(
            'Changes since base version: %s' %
            self.target_version.get_googlesource_diff_link(self.base_version))

        self._update_package_version()

        try:
            terminal.run_npm_command('init')

            # When no conflicts come back, we can proceed with the
            # update_patches.
            if self._run_update_patches_with_no_deletions() is not True:
                return False
        except subprocess.CalledProcessError as e:
            if ('There were some failures during git reset of specific '
                    'repo paths' in e.stderr):
                logging.warning(
                    '[bold cyan]npm run init[/] is failing to reset some'
                    ' paths. This could be happening because of a bad sync'
                    'state before starting the upgrade.')

            if (e.returncode != 0
                    and 'Exiting as not all patches were successful!'
                    in e.stderr.splitlines()[-1]):
                resolver = PatchFailureResolver()
                resolver.apply_patches_3way(target_version=self.target_version,
                                            launch_vscode=launch_vscode)
                if resolver.requires_conflict_resolution() is True:
                    # Manual resolution required.
                    console.log(
                        '👋 (Address all sections with '
                        f'{ACTION_NEEDED_DECORATOR} above, and then rerun '
                        '[italic]🚀Brockit![/] with [bold cyan]'
                        '--continue[/])')
                    return False

                if self._run_update_patches_with_no_deletions() is not True:
                    return False

                resolver.stage_all_patches()
                self._save_conflict_resolved_patches()

                # With all conflicts resolved, it is necessary to close the
                # upgrade with all the same steps produced when running an
                # upgrade continuation, as recovering from a conflict-
                # resolution failure.
                return self._continue(no_conflict_continuation=True)
            if e.returncode != 0:
                logging.error('Failures found when running npm run init\n%s',
                              e.stderr)
                return False

        self._save_updated_patches()

        terminal.run_npm_command('chromium_rebase_l10n')
        self._save_rebased_l10n()

        return True

    # The argument list differs here because that's the way we get args through
    # Task into the derived methods. Maybe something better can be done here.
    # pylint: disable=arguments-differ
    def execute(self, no_conflict_continuation: bool, launch_vscode: bool,
                with_github: bool) -> bool:
        """Executes the upgrade process.

    Keep in this function all code that is common to both start and continue.

    Args:
        no_conflict_continuation:
            Indicates that a continuation does not produce a conflict-resolved
            change.
        launch_vscode:
            Indicates the user wants to launch vscode with the patches that
            require manual conflict resolution.
        with_github:
            Indicates the user wants to create or update the github issue for
            the upgrade.
        """
        if self.target_version == self.working_version:
            logging.error(
                'This branch is already in %s. (Maybe you meant to pass [bold '
                'cyan]--continue[/]?)', self.target_version)
            return False

        if self.target_version < self.working_version:
            logging.error('Cannot upgrade version from %s to %s',
                          self.target_version, self.working_version)
            return False

        if not self.is_continuation:
            # We initialise the continuation file here rather than in the
            # constructor to avoid overwritting the file if the user made the
            # mistake of calling brockit again without `--continue`.
            ContinuationFile(target_version=self.target_version,
                             working_version=self.working_version,
                             base_version=self.base_version).save()

        if with_github is True and _is_gh_cli_logged_in() is False:
            # Fail early if gh cli is not logged in.
            logging.error('GitHub CLI is not logged in.')
            return False

        if self.is_continuation:
            if self.target_version != self.chromium_src_version:
                logging.error(
                    'To run with [bold cyan]--continue[/] the Chromium '
                    'version has to be in Sync with Brave.'
                    ' Brave %s ➜ Chromium %s', self.target_version,
                    self.chromium_src_version)
                return False

            result = self._continue(
                no_conflict_continuation=no_conflict_continuation)
        else:
            result = self._start(launch_vscode=launch_vscode)

        if result is True and with_github is True:
            return GitHubIssue(base_version=self.base_version,
                               target_version=self.target_version
                               ).create_or_updade_version_issue()

        return result


def _find_from_ref_version(from_ref) -> Version:
    """ Finds the version from a reference.

    This function resolves the value provided to --from-ref into a Version
    whenver that's possible. It also will handle the tags with special meaning
    like @upstream and @previous.
    """
    if from_ref == "@upstream":
        result = Version.from_upstream()
        if result is None:
            logging.error(
                'Could not determine the upstream branch. (Maybe set [bold '
                'cyan]--set-upstream-to[/] in your branch?)')
            sys.exit(1)
        return result

    if from_ref == "@previous":
        return Version.from_previous()

    if not Repository.brave().is_valid_git_reference(from_ref):
        logging.error(
            'Value provided to [bold cyan]--base-from[/] is not a valid git '
            'ref: %s', from_ref)
        sys.exit(1)
    return Version.from_git(from_ref)


def show(args: argparse.Namespace):
    """Prints various insights about brave-core.

    This is a helper command line that allows us to inspect a few things about
    brave-core and how brockit process things.
    """
    if args.package_version:
        console.print(f'upstream version: {Version.from_git("HEAD")}')
    if args.from_ref_value is not None:
        from_ref_value = _find_from_ref_version(args.from_ref_value)
        if from_ref_value is not None:
            console.print(f'base version: {from_ref_value}')
    if args.log_link:
        console.print('googlesource link: %s' %
                      Version.from_git('HEAD').get_googlesource_diff_link(
                          Version.from_previous()))
    return 0

def main():
    # This is a global parser with arguments that apply to every function.
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Produces verbose logs (full command lines being executed, etc).')
    global_parser.add_argument(
        '--infra-mode',
        action='store_true',
        help=
        ('Indicates that the script is being run in the infra environment. '
         'This changes the script output, specially providing feedback for the '
         'CI to be kept alive.'),
        dest='infra_mode')

    # The `--from-ref` parse is used by multiple operations.
    base_version_parser = argparse.ArgumentParser(add_help=False)
    base_version_parser.add_argument(
        '--from-ref',
        help=
        'A reference to the version that the upgrade is coming from. This is '
        'a git branch, hash, tag, etc, or one of the special values: @upstream'
        ' (upstream branch), @previous (the previous version from HEAD). '
        'Defaults to @upstream.',
        default=None)

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='command', required=True)
    lift_parser = subparsers.add_parser(
        'lift',
        parents=[global_parser, base_version_parser],
        help='Upgrade the chromium base version.')
    lift_parser.add_argument('--to',
                             required=True,
                             help='The branch used as the base version.')
    lift_parser.add_argument(
        '--continue',
        action='store_true',
        help='Resumes from manual patch conflict resolution.',
        dest='is_continuation')
    lift_parser.add_argument(
        '--restart',
        action='store_true',
        help='Resumes from manual patch conflict resolution.')
    lift_parser.add_argument(
        '--with-github',
        action='store_true',
        help='Creates or updates the github for this branch.',
        dest='with_github')
    lift_parser.add_argument(
        '--vscode',
        action='store_true',
        help=
        'Launches vscode for manual conflict resolution and similar issues.')
    lift_parser.add_argument(
        '--no-conflict-change',
        action='store_true',
        help='Indicates that a continuation does not have conflict patches to '
        'commit any longer.',
        dest='no_conflict')

    subparsers.add_parser(
        'regen',
        parents=[global_parser, base_version_parser],
        help='Regenerates all patches and strings for the current branch.')

    subparsers.add_parser(
        'update-version-issue',
        parents=[global_parser, base_version_parser],
        help='Creates or updates the GitHub issue for the corrent branch.')

    show_parser = subparsers.add_parser(
        'show', help='Prints various insights about brave-core.')
    show_parser.add_argument(
        '--package-version',
        action='store_true',
        help='Shows the current Chromium version in package.')
    show_parser.add_argument(
        '--from-ref-value',
        help='Shows the Chromium version from a git reference.',
        default=None,
        dest='from_ref_value')
    show_parser.add_argument('--log-link',
                             action='store_true',
                             help='Prints the git log links to googlesource.')

    subparsers.add_parser('reference',
                          help='Detailed documentation for this tool.')
    args = parser.parse_args()

    def has_verbose():
        return hasattr(args, 'verbose') and args.verbose

    logging.basicConfig(
        level=logging.DEBUG if has_verbose() else logging.INFO,
        format='%(message)s',
        handlers=[IncendiaryErrorHandler(markup=True, rich_tracebacks=True)])

    if hasattr(args, 'infra_mode') and args.infra_mode:
        terminal.set_infra_mode()

    if hasattr(args, 'from_ref'):
        if args.command == 'lift' and args.is_continuation:
            if args.from_ref is not None:
                parser.error(
                    'Switch --from-ref not supported with --continue.')

    def get_resolved_from_ref():
        return _find_from_ref_version(
            args.from_ref if args.from_ref is not None else '@upstream')

    if args.command == 'lift' and args.no_conflict and not args.is_continuation:
        parser.error('--no-conflict-change can only be used with --continue')
    if args.command == 'lift' and args.restart and args.is_continuation:
        parser.error('--restart does not support --continue')

    if args.command == 'lift':
        if args.restart:
            if not ReUpgrade(Version(args.to)).run():
                return 1

        if not args.is_continuation:
            upgrade = Upgrade(Version(args.to), args.is_continuation,
                              get_resolved_from_ref())
        else:
            upgrade = Upgrade(Version(args.to), args.is_continuation)

        return upgrade.run(args.no_conflict, args.vscode, args.with_github)
    if args.command == 'regen':
        return Regen(get_resolved_from_ref()).run()
    if args.command == 'update-version-issue':
        return GitHubIssue(get_resolved_from_ref()).run()
    if args.command == 'reference':
        return console.print(Markdown(__doc__))
    if args.command == 'show':
        return show(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
