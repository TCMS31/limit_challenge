# Flows

The Next.js app on port 3000 calls the Django API on port 8000. The access token stays in memory. The refresh token stays in the `fleet_refresh` cookie.

## Sign in

```mermaid
flowchart TD
  open[Open the app] --> restore[Call refresh with the fleet_refresh cookie]
  restore -->|cookie valid| home[Vehicle search]
  restore -->|no cookie or expired| login[Sign in as fleet]
  login --> token[API returns an access token and sets the refresh cookie]
  token --> home
  home --> call[Any API call sends the bearer access token]
  call -->|token valid| ok[Request proceeds]
  call -->|401| refresh[Refresh once using the cookie]
  refresh -->|new access token| call
  refresh -->|cookie invalid| login
  home --> logout[Sign out]
  logout --> clear[Blacklist the refresh token and clear the cookie]
  clear --> login
```

Sign-in is the only step that sends the password. `/admin/` uses a separate staff account from `createsuperuser`.

## Set up the fleet

Offices, mechanics, and maintenance records are created through the API or Django admin. The UI creates and edits vehicles.

```mermaid
flowchart TD
  office[Create an office: name and city] --> mechanic[Create a mechanic: name, certification number, active flag]
  mechanic --> dup[Check VIN and license plate]
  dup -->|conflicts empty| vehicle[Create a vehicle at that office]
  dup -->|vin or license_plate| stop[Fix the conflict and check again]
  stop --> dup
  vehicle --> active{Vehicle active?}
  active -->|yes| plate[License plate must be unique among active vehicles]
  active -->|no| share[Plate may match an inactive vehicle]
```

A VIN is unique for every vehicle, active or not.

## Record maintenance

```mermaid
flowchart TD
  pick[Choose an active vehicle and an active mechanic] --> job[Create a maintenance record]
  job --> fields[Date, type, cost, notes]
  fields --> type{Type}
  type --> oil[oil_change]
  type --> inspection[inspection]
  type --> repair[repair]
  type --> tires[tires]
  fields --> cost{Cost}
  cost -->|zero or more| saved[(Saved on the vehicle)]
  cost -->|negative| rejected[400: cost cannot be negative]
  saved --> history[Vehicle detail and maintenance history, newest first]
```

Deleting an office, vehicle, or mechanic that still has records is rejected. Remove or reassign those rows first.

## Move a vehicle

```mermaid
flowchart TD
  detail[Open the vehicle] --> assign[Assign a new office]
  assign --> only[Only the office field changes]
  only --> summary[Office summary counts the vehicle under the new office]
```

Assign does not write a history of past offices and does not change maintenance records.

## Find work

```mermaid
flowchart TD
  search[Search vehicles] --> filters[Office, active, make, model, dates, certification]
  filters --> same[Dates and certification must match one maintenance job]
  same --> list[Paginated vehicle list]

  due[Needs maintenance] --> rule{Active vehicle}
  rule -->|never serviced| first[Listed first]
  rule -->|last service more than 365 days ago| next[Listed after never-serviced]
  rule -->|serviced within 365 days| hide[Left off the list]

  offices[Office summary] --> stats[Active vehicle count, rolling 365-day cost, latest maintenance date]
  workload[Mechanic workload] --> year[Jobs and cost for the current calendar year, busiest first]
```

Make and model match any case-insensitive fragment, so `toy` finds `Toyota`.

## Admin

A staff user signs in at `/admin/`. The home page charts active vehicles by office, maintenance cost over the same rolling year as the office summary, and the ten busiest mechanics this year. Offices, vehicles, mechanics, and maintenance records can be edited there.
