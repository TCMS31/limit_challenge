# Assumptions

- Maintenance type is `oil_change`, `inspection`, `repair`, or `tires`. The challenge left the type open.
- A license plate is unique only among active vehicles. Inactive vehicles may share one. A VIN is unique for every vehicle.
- Make and model search matches a case-insensitive fragment, because those filters are free-text boxes. `toy` finds `Toyota`.
- The API requires JWT even though the challenge said authentication was unnecessary. `/healthz/` stays public.
- The demo API user `fleet` / `fleet-demo` is created by `seed_fleet`, not by Compose startup. That user is not staff.

