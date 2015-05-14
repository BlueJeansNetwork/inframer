# Inframer

# Distributed infrastructure
  - Config management - chef
  - Monitoring - nagios, icinga
  - On premise infrastructure - VMware
  - Cloud infrastructure - AWS

# The good news
  - Every infrastructure component does one thing and does it well
  - Rich APIs to perform CRUD operations
  - REST APIs - language agnostic

# The bad news
  - APIs queried by standalone tools
  - They cannot talk to each other 
  - They should not talk to each other 
  - Every organization duplicates the effort

# The Question
  - What if I had a central aggregator which talks to all of my APIs?

# Growing need to corelate information 
  - All info under one roof
    - Input: IP Address
    - Output:
      - Which ESX host does it belong to?
      - What role does it fulfill? - App, database, none
      - Which rack is it on and which switch is it connected to?
      - More. More. More.
  - Diff/Intersect various databases
    - Provisioned but not cheffed
    - Provisioned, cheffed but not monitored
  - Validate assumptions about uniformity
    - Are all of my infrastructure databases in sync?
    - Are all of my nodes in use?
    - Do all of my nodes have the right roles?

# Enter Inframer
  - Simple, extensible tool to centralize the power of APIs
  - Collect information from various databases
  - Dump them in a central location
  - Query the centre and co-relate information

# Architecture
  - Collectors collect information
  - Dump them in a central mongodb
  - REST APIs exposes this information in a unified way
  - Analyzers are clients - command line tools, dashboards
  - They consume the REST APIs and co-relate information
  - Extend it by writing your own collectors, analyzers

# Demo

# Advantages
  - An generic aggregator powered by your collectors
  - Central place to write your collectors
  - Access to community collectors for already solved problems
  - Extensible as per your own needs

# Conclusion
  - Not a replacement for CMDB
  - Get your APIs to work coherently
  - Make it easier for new DevOps Engineer to understand your infrastructure
