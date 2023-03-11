"""Utility functions."""

import contextlib
import datetime
import getpass
import glob
import os
import pwd
import random
import shutil
import stat
import string
import subprocess
import sys
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from . import config_dict_template


ENV = {}
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)


class FatalError(Exception):

    """A simple exception."""

    pass


def user_input(message):
    """Ask something to the user."""
    try:
        from builtins import input
    except ImportError:
        answer = raw_input(message)
    else:
        answer = input(message)
    return answer


def exec_cmd(cmd, sudo_user=None, pinput=None, login=True, **kwargs):
    """Execute a shell command.
    Run a command using the current user. Set :keyword:`sudo_user` if
    you need different privileges.
    :param str cmd: the command to execute
    :param str sudo_user: a valid system username
    :param str pinput: data to send to process's stdin
    :rtype: tuple
    :return: return code, command output
    """
    sudo_user = ENV.get("sudo_user", sudo_user)
    if sudo_user is not None:
        cmd = "sudo {}-u {} {}".format("-i " if login else "", sudo_user, cmd)
    if "shell" not in kwargs:
        kwargs["shell"] = True
    if pinput is not None:
        kwargs["stdin"] = subprocess.PIPE
    capture_output = False
    if "capture_output" in kwargs:
        capture_output = kwargs.pop("capture_output")
    elif not ENV.get("debug"):
        capture_output = True
    if capture_output:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = None
    process = subprocess.Popen(cmd, **kwargs)
    if pinput or capture_output:
        c_args = [pinput] if pinput is not None else []
        output = process.communicate(*c_args)[0]
    else:
        process.wait()
    return process.returncode, output


def dist_info():
    """Try to return information about the system we're running on."""
    path = "/etc/os-release"
    if os.path.exists(path):
        info = {}
        with open(path) as fp:
            for line in fp.readlines():
                if line == '\n':
                    continue
                key, value = line.split("=")
                value = value.rstrip('"\n')
                value = value.strip('"')
                info[key] = value
        return info["NAME"], info["VERSION_ID"]
    printcolor(
        "Failed to retrieve information about your system, aborting.",
        RED)
    sys.exit(1)


def dist_name():
    """Try to guess the distribution name."""
    return dist_info()[0].lower()


def mkdir(path, mode, uid, gid):
    """Create a directory."""
    if not os.path.exists(path):
        os.mkdir(path, mode)
    else:
        os.chmod(path, mode)
    os.chown(path, uid, gid)


def mkdir_safe(path, mode, uid, gid):
    """Create a directory. Safe way (-p)"""
    if not os.path.exists(path):
        os.makedirs(os.path.abspath(path), mode)
    mkdir(path, mode, uid, gid)


def make_password(length=16):
    """Create a random password."""
    return "".join(
        random.SystemRandom().choice(
            string.ascii_letters + string.digits) for _ in range(length))


@contextlib.contextmanager
def settings(**kwargs):
    """Context manager to declare temporary settings."""
    for key, value in kwargs.items():
        ENV[key] = value
    yield
    for key in kwargs.keys():
        del ENV[key]


class ConfigFileTemplate(string.Template):

    """Custom class for configuration files."""

    delimiter = "%"


def backup_file(fname):
    """Create a backup of a given file."""
    for f in glob.glob("{}.old.*".format(fname)):
        os.unlink(f)
    bak_name = "{}.old.{}".format(
        fname, datetime.datetime.now().isoformat())
    shutil.copy(fname, bak_name)


def copy_file(src, dest):
    """Copy a file to a destination and make a backup before."""
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(src))
    if os.path.isfile(dest):
        backup_file(dest)
    shutil.copy(src, dest)


def copy_from_template(template, dest, context):
    """Create and copy a configuration file from a template."""
    now = datetime.datetime.now().isoformat()
    with open(template) as fp:
        buf = fp.read()
    if os.path.isfile(dest):
        backup_file(dest)
    with open(dest, "w") as fp:
        fp.write(
            "# This file was automatically installed on {}\n"
            .format(now))
        fp.write(ConfigFileTemplate(buf).substitute(context))


def check_config_file(dest, interactive=False, upgrade=False, backup=False, restore=False):
    """Create a new installer config file if needed."""
    is_present = True
    if os.path.exists(dest):
        return is_present, update_config(dest, False)
    if upgrade:
        printcolor(
            "You cannot upgrade an existing installation without a "
            "configuration file.", RED)
        sys.exit(1)
    elif backup:
        is_present = False
        printcolor(
            "Your configuration file hasn't been found. A new one will be generated. "
            "Please edit it with correct password for the databases !", RED)
    elif restore:
        printcolor(
            "You cannot restore an existing installation without a "
            f"configuration file. (file : {dest} has not been found...", RED)
        sys.exit(1)

    printcolor(
        "Configuration file {} not found, creating new one."
        .format(dest), YELLOW)
    gen_config(dest, interactive)
    return is_present, None


def has_colours(stream):
    """Check if terminal supports colors."""
    if not hasattr(stream, "isatty"):
        return False
    if not stream.isatty():
        return False  # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum("colors") > 2
    except:
        # guess false in case of error
        return False


has_colours = has_colours(sys.stdout)


def printcolor(message, color):
    """Print a message using a green color."""
    if has_colours:
        message = "\x1b[1;{}m{}\x1b[0m".format(30 + color, message)
    print(message)


def error(message):
    """Print error message."""
    printcolor(message, RED)


def success(message):
    """Print success message."""
    printcolor(message, GREEN)


def convert_version_to_int(version):
    """Convert a version string to an integer."""
    number_bits = (8, 8, 16)

    numbers = [int(number_string) for number_string in version.split(".")]
    if len(numbers) > len(number_bits):
        raise NotImplementedError(
            "Versions with more than {0} decimal places are not supported"
            .format(len(number_bits) - 1)
        )
    # add 0s for missing numbers
    numbers.extend([0] * (len(number_bits) - len(numbers)))
    # convert to single int and return
    number = 0
    total_bits = 0
    for num, bits in reversed(list(zip(numbers, number_bits))):
        max_num = (bits + 1) - 1
        if num >= 1 << max_num:
            raise ValueError(
                "Number {0} cannot be stored with only {1} bits. Max is {2}"
                .format(num, bits, max_num)
            )
        number += num << total_bits
        total_bits += bits
    return number


def random_key(l=16):
    """Generate a random key.

    :param integer l: the key's length
    :return: a string
    """
    punctuation = """!#$%&()*+,-./:;<=>?@[]^_`{|}~"""
    population = string.digits + string.ascii_letters + punctuation
    while True:
        key = "".join(random.sample(population * l, l))
        if len(key) == l:
            return key


def validate(value, config_entry):
    if value is None:
        return False
    if "values" not in config_entry and "validators" not in config_entry:
        return True
    if "values" in config_entry:
        try:
            value = int(value)
        except ValueError:
            return False
        return value >= 0 and value < len(config_entry["values"])
    if "validators" in config_entry:
        for validator in config_entry["validators"]:
            valide, message = validator(value)
            if not valide:
                printcolor(message, MAGENTA)
                return False
        return True


def get_entry_value(entry, interactive):
    if callable(entry["default"]):
        default_value = entry["default"]()
    else:
        default_value = entry["default"]
    user_value = None
    if entry.get("customizable") and interactive:
        while (user_value != '' and not validate(user_value, entry)):
            question = entry.get("question")
            if entry.get("values"):
                question += " from the list"
                values = entry.get("values")
                for index, value in enumerate(values):
                    question += "\n{}   {}".format(index, value)
            print(question)
            print("default is <{}>".format(default_value))
            user_value = user_input("-> ")

        if entry.get("values") and user_value != "":
            user_value = values[int(user_value)]
    return user_value if user_value else default_value


def load_config_template(interactive):
    """Instantiate a configParser object with the predefined template."""
    tpl_dict = config_dict_template.ConfigDictTemplate
    config = configparser.ConfigParser()
    # only ask about options we need, else still generate default
    for section in tpl_dict:
        if "if" in section:
            config_key, value = section.get("if").split("=")
            section_name, option = config_key.split(".")
            interactive_section = (
                config.get(section_name, option) == value and interactive)
        else:
            interactive_section = interactive
        config.add_section(section["name"])
        for config_entry in section["values"]:
            value = get_entry_value(config_entry, interactive_section)
            config.set(section["name"], config_entry["option"], value)
    return config


def update_config(path, apply_update=True):
    """Update an existing config file."""
    config = configparser.ConfigParser()
    with open(path) as fp:
        config.read_file(fp)
    new_config = load_config_template(False)

    old_sections = config.sections()
    new_sections = new_config.sections()

    update = False

    dropped_sections = list(set(old_sections) - set(new_sections))
    added_sections = list(set(new_sections) - set(old_sections))
    if len(dropped_sections) > 0 and apply_update:
        printcolor("Following section(s) will not be ported "
                   "due to being deleted or renamed: " +
                   ', '.join(dropped_sections),
                   RED)

    if len(dropped_sections) + len(added_sections) > 0:
        update = True

    for section in new_sections:
        if section in old_sections:
            new_options = new_config.options(section)
            old_options = config.options(section)

            dropped_options = list(set(old_options) - set(new_options))
            added_options = list(set(new_options) - set(old_options))
            if len(dropped_options) > 0 and apply_update:
                printcolor(f"Following option(s) from section: {section}, "
                           "will not be ported due to being "
                           "deleted or renamed: " +
                           ', '.join(dropped_options),
                           RED)
            if len(dropped_options) + len(added_options) > 0:
                update = True

            if apply_update:
                for option in new_options:
                    if option in old_options:
                        value = config.get(section, option, raw=True)
                        if value != new_config.get(section, option, raw=True):
                            update = True
                            new_config.set(section, option, value)

    if update and apply_update:
        # Backing up old config file
        date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        dest = f"{os.path.splitext(path)[0]}_{date}.old"
        shutil.copy(path, dest)

        # Overwritting old config file
        with open(path, "w") as configfile:
            new_config.write(configfile)

        # Set file owner to running u+g, and set config file permission to 600
        current_username = getpass.getuser()
        current_user = pwd.getpwnam(current_username)
        os.chown(dest, current_user[2], current_user[3])
        os.chmod(dest, stat.S_IRUSR | stat.S_IWUSR)

        return dest
    elif update and not apply_update:
        # Simply check if current config file is outdated
        return True
    elif not update and not apply_update:
        return False

    return None


def gen_config(dest, interactive=False):
    """Create config file from dict template"""
    config = load_config_template(interactive)

    with open(dest, "w") as configfile:
        config.write(configfile)

    # Set file owner to running user and group, and set config file permission to 600
    current_username = getpass.getuser()
    current_user = pwd.getpwnam(current_username)
    os.chown(dest, current_user[2], current_user[3])
    os.chmod(dest, stat.S_IRUSR | stat.S_IWUSR)


def validate_backup_path(path: str, silent_mode: bool):
    """Check if provided backup path is valid or not."""
    path_exists = os.path.exists(path)
    if path_exists and os.path.isfile(path):
        printcolor(
            "Error, you provided a file instead of a directory!", RED)
        return None

    if not path_exists:
        if not silent_mode:
            create_dir = input(
                f"\"{path}\" doesn't exist, would you like to create it? [Y/n]\n"
            ).lower()

        if silent_mode or (not silent_mode and create_dir.startswith("y")):
            pw = pwd.getpwnam("root")
            mkdir_safe(path, stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])
        else:
            printcolor(
                "Error, backup directory not present.", RED
            )
            return None

    if len(os.listdir(path)) != 0:
        if not silent_mode:
            delete_dir = input(
                "Warning: backup directory is not empty, it will be purged if you continue... [Y/n]\n").lower()

        if silent_mode or (not silent_mode and delete_dir.startswith("y")):
            try:
                os.remove(os.path.join(path, "installer.cfg"))
            except FileNotFoundError:
                pass

            shutil.rmtree(os.path.join(path, "custom"),
                          ignore_errors=False)
            shutil.rmtree(os.path.join(path, "mails"), ignore_errors=False)
            shutil.rmtree(os.path.join(path, "databases"),
                          ignore_errors=False)
        else:
            printcolor(
                "Error: backup directory not clean.", RED
            )
            return None

    backup_path = path
    pw = pwd.getpwnam("root")
    for dir in ["custom/", "databases/"]:
        mkdir_safe(os.path.join(backup_path, dir),
                   stat.S_IRWXU | stat.S_IRWXG, pw[2], pw[3])
    return backup_path
