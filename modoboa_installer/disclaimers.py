from . import utils


def installation_disclaimer(args, config):
    """Display installation disclaimer."""
    hostname = config.get("general", "hostname")
    utils.printcolor(
        "Notice:\n"
        "It is recommanded to run this installer on a FRESHLY installed server.\n"
        "(ie. with nothing special already installed on it)\n",
        utils.CYAN
        )
    utils.printcolor(
        "Warning:\n"
        "Before you start the installation, please make sure the following "
        "DNS records exist for domain '{}':\n"
        "  {} IN A   <IP ADDRESS OF YOUR SERVER>\n"
        "     @ IN MX  {}.\n".format(
            args.domain,
            hostname.replace(".{}".format(args.domain), ""),
            hostname
            ),
        utils.YELLOW
        )
    utils.printcolor(
            "Your mail server will be installed with the following components:",
            utils.BLUE)


def upgrade_disclaimer(config):
    """Display upgrade disclaimer."""
    utils.printcolor(
        "Your mail server is about to be upgraded and the following components"
        " will be impacted:", utils.BLUE
        )


def backup_disclaimer():
    """Display backup disclamer. """
    utils.printcolor(
        "Your mail server will be backed up locally.\n"
        " !! You should really transfer the backup somewhere else...\n"
        " !! Custom configuration (like for postfix) won't be saved.", utils.BLUE)


def restore_disclaimer():
    """Display restore disclamer. """
    utils.printcolor(
        "You are about to restore a previous installation of Modoboa.\n"
        "If a new version has been released in between, please update your database!",
        utils.BLUE)
