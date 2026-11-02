# Home Server Add-ons

Home Assistant add-on repository used by the home server installer.

- `smartir` — copies the [SmartIR](https://github.com/smartHomeHub/SmartIR) custom integration (MIT) into
  `custom_components/smartir`. Runs once and stops; Home Assistant must restart to load it.
  A `smartir` folder installed by other means (no `.installed_by_addon` marker) is never touched.
