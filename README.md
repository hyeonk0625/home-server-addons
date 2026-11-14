# Home Server Add-ons

Home Assistant add-on repository used by the home server installer.

- `smartir` — copies the [SmartIR](https://github.com/smartHomeHub/SmartIR) custom integration (MIT) into
  `custom_components/smartir`. Runs once and stops; Home Assistant must restart to load it.
  A `smartir` folder installed by other means (no `.installed_by_addon` marker) is never touched.
- `user_integrations` — copies pinned custom integrations into `custom_components/<domain>`: [Winix](https://github.com/iprak/winix)
  2.0.2 (MIT), [SonoffLAN](https://github.com/AlexxIT/SonoffLAN) 3.13.3 (MIT), [Dreame Vacuum](https://github.com/Tasshack/dreame-vacuum)
  2.0.3 (MIT) and [Coway IoCare](https://github.com/RobertD502/home-assistant-iocare) 0.6.5 (MIT), each pinned by commit and archive sha256,
  plus our own `login_relay` (vendor account login through the seller relay), shipped in the add-on folder.
  Runs once and stops; Home Assistant must restart to load them. A folder installed by other means (no `.installed_by_addon`
  marker) is never touched.
