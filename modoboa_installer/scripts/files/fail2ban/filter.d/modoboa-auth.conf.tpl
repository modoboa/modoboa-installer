# Fail2Ban filter Modoboa authentication

[INCLUDES]

before = common.conf

[Definition]

failregex = modoboa\.auth: WARNING Failed connection attempt from \'<HOST>\' as user \'.*?\'$
