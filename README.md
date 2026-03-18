# beetmove-telemetry
Scripts to upload semanticdb-kotlinc releases to https://maven.mozilla.org/

# Example of usage
```bash
$ cp config_example.json script_config.json
$ < update script_config with actual credentials > ...
$ VERSION='0.9.0'; uv run --with-requirements requirements.txt script.py \
                                     --script-config script_config.json \
                                     --bucket maven-production \
                                     --version "$VERSION"
```

# Branches
- [main](https://github.com/mozilla-releng/beetmove-telemetry/tree/main): @mtabara's work for glean
- [apidoc](https://github.com/mozilla-releng/beetmove-telemetry/tree/apidoc): @escapewindow's work for apidoc
- [mozsearch](https://github.com/mozilla-releng/beetmove-telemetry/tree/mozsearch): @jcristau's work for semanticdb-kotlinc
