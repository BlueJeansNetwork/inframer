# Inframer - Know thy infra

---

# Problem

- How do i co-relate information in my distributed infrastrucutre?

---

# Distributed infrastructure

- 1 node - multiple databases
- Database: where infra info resides e.g. Chef, VMware, etc.
- Config management - Chef
- Monitoring - Icinga
- On premise infra - VMware
- Cloud infra - AWS
- Inventory, IT assets, network connectivity - Device42
- Others

---

# The good parts

- Each database does one thing and does it right
- Provide rich REST APIs
- Useful libraries built over these APIs - boto, pychef, etc.

---

# The pain points

- Knowledge trapped in silos
- APIs don't talk to each other
- They shouldn't

---

# But..

- Don't you wish they could?
- Don't you wish you could co-relate their information?
- Don't you wish...

---

# You had a tool which...

- Gives you information about that node in chef, icinga, etc.
- Does a diff/intersection of various databases
  <pre>
  Give me all the AWS nodes in us-west-1 region 
  which are running 
  but not yet monitored
  </pre>
- validates your assumptions about your data consistency

---

# Enter Inframer

- Created to scratch our itch
- Python, Flask, Redis
- 2 hackathons / 48 hours
- Team
  <pre>
  Ravi Ranjan
  Saurabh Bathe
  Saurabh Hirani
  Virendra Bhalothia
  </pre> 
- Added to the DevOps roadmap

---

# One line description:

- Collect, store, analyze

---

# Architecture:

<img src="http://127.0.0.1:3999/images/arch.png" style="width: 900px; height: 900px"/>

---

# Collectors

- Collect information from each database - return json
- Each database has one or many views e.g. chef has environments, nodes
- Extensible - write your own collectors

---

# Stores

- Collectors dump information in stores - current store - Redis
- Current implementation - Redis
- Collectors decoupled from stores

---

# REST API

- REST API built on top of store
- Query the dumped data and present individual and aggregate information

<pre>
  /inframer/api/v1/db
  /inframer/api/v1/db/aws
  /inframer/api/v1/db/aws/region/
  /inframer/api/v1/db/aws/region/us-east-1/i-9999xy1
</pre>

- Filters for getting data subsets

---

# Demo

- REST API

---

# Analyzers

- Command line tools on top of the REST APIs
- Query individual databases, perform set operations
  <pre>
  Give me all the AWS nodes in us-west-1 region 
  which are running, monitored but not yet cheffed
  </pre>
- Extensible - write your own analyzers

---

# Secret ingredient - You

- No two infrastructure layouts are alike
- More databases - write new collectors
- Analytics - write new analyzers
- Fit the tool to your needs

---

# Conclusion

- Growing need to co-relate information - in a generic way
- Collate information collected by your APIs and make sense of it
- Central source of examples

---

# Thank you - Q & A

- <a href="https://github.com/BlueJeansNetwork/inframer">https://github.com/BlueJeansNetwork/inframer</a>
- saurabhhirani@bluejeansnet.com
- We are BlueJeans Network
- An interoperable cloud based video conferencing service
- We make video conferencing easier

---

# Roadmap

- Granular updates - right now - create, flush, re-create
- Better search capabilities - full text, fuzzy values
- Test if it fits different infra layouts
