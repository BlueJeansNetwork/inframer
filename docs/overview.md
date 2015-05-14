# What is this talk about:
  - getting data from multiple sources of infrastructure information under one roof
  - having an extensible framework - which developers can use to extend this capability for future infrastructure databases

# Material to cover:
  - Problem we are trying to solve:
    - Infrastructure information spread across multiple databases
      - e.g. chef - config management, icinga - monitoring, vmware - on premise infrastructure, etc.
    - Each has an API - but none of them work with the other
    - Everyone has programs written to use these APIs and get information but they are lying in isolation
    - There is no current way to validate what is in use where
  - Solution:
    - Inframer - infrastructure informer
  - Architecture overiew:
    - Collectors collect information e.g query chef to get node data, query nagios to get monitoring data
    - REST API reports this information e.g. generic structure
    - Dashboard built on top of REST APIs to show the collected data
    - You can build your own analyzers crunch the information and give knowledge like:
      - which node is present in chef but not monitored
      - how many vmware nodes are not yet cheffed

# Key insight:
  - No. of infrastructure databases will keep on increasing
  - Growing need to consolidate this information
  - Having an inframer like tool will help you gain insight and have your way with the gathered information
  - Will also bring in examples of querying multiple infrastructure components under one roof
