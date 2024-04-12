import dynaconf

config = dynaconf.Dynaconf(
    settings_file=["config-defaults.toml", "config.toml"],
    envvar_prefix="CKP_",
    load_dotenv=True,
    merge_enabled=True,
)
