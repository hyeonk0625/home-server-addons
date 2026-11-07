# Home Server Add-ons

Home Assistant add-on repository used by the home server installer.

- `smartir` — copies the [SmartIR](https://github.com/smartHomeHub/SmartIR) custom integration (MIT) into
  `custom_components/smartir`. Runs once and stops; Home Assistant must restart to load it.
  A `smartir` folder installed by other means (no `.installed_by_addon` marker) is never touched.
- `user_integrations` — copies pinned custom integrations into `custom_components/<domain>`: [Winix](https://github.com/iprak/winix)
  2.0.2 (MIT) and [SonoffLAN](https://github.com/AlexxIT/SonoffLAN) 3.13.3 (MIT), each pinned by commit and archive sha256.
  Runs once and stops; Home Assistant must restart to load them. A folder installed by other means (no `.installed_by_addon`
  marker) is never touched.
