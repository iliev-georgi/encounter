# Encounter


## Vision

The aim of this project is to build a live knowledge graph of manually curated data points describing human-bird encounters. The data is made available via a standard endpoint to explore and embed into downstream applications.


## The lingo

Throughout the code and the enabling materials we work with the following central concepts

- __Encounter__
  
  The physical act of observing an object of interest (e.g. a bird) in the real world. It is grounded in place and time and has some additional properties helping systems handle the encounter's digital representation effectively

- __Evidence__

  The digital evidence documenting an encounter. This could be a photograph, a log book entry, or any other material referring to the encounter taking place. Evidence is collected and managed in an external system (e.g. a social network with photo sharing capability)

-  __Knowledge graph__

   The collection of integrated data points linking formal encounter representations to the evidence from an external system and to entries from a specialized information system (e.g. an ontology for managing the scientific and common names of birds)


## Semantic model

### Namespaces
```
@prefix encounter: <https://encounter.pastabytes.com/v0.1.0/> .
@prefix encounter-location: <https://encounter.pastabytes.com/v0.1.0/location/> .
@prefix encounter-ontology: <https://encounter.pastabytes.com/v0.1.0/ontology/> .
@prefix pixelfed: <https://pixelfed.pastabytes.com/> .
```

### As-built `Encounter` model
```mermaid
---
config:
  theme: neutral
---
%%{init: {
  "themeCSS": [
    "[id|=entity-Evidence] .er.entityBox { fill: lightgreen;} ",
    "[id|=entity-Location] .er.entityBox { fill: powderblue;} ",
    "[id|=entity-User] .er.entityBox { fill: lightgreen;} ",
    "[id|=entity-Encounter] .er.entityBox { fill: powderblue;} ",
    "[id|=entity-Bird] .er.entityBox { fill: teal;} ",
    "[id*=itude] .er.entityBox { fill: antiqueWhite;} ",
    "[id|=entity-Time] .er.entityBox { fill: antiqueWhite;} "
    ]
}}%%

erDiagram
    Encounter["encounter:id/1"]
    EncounterClass["encounter-ontology:Encounter"]
    Location["encounter-location:0475...47bb"]
    LocationClass["encounter-ontology:Location"]
    Latitude["42.698334^^xsd:float"]
    Longitude["23.319941^^xsd:float"]
    Time["1736602800^^xsd:long"]
    User["pixelfed:iliev.georgi"]
    UserClass["encounter-ontology:User"]
    Evidence["pixelfed:storage/m/_v2/7788...2TKG.jpg"]
    EvidenceClass["encounter-ontology:Evidence"]
    Bird["<http://www.yso.fi/onto/avio/e818>"]
    BirdClass["encounter-ontology:Bird"]

    Encounter ||--|{ EncounterClass : a

    Location ||--|{ LocationClass : a

    Location ||--|| Latitude : "encounter-ontology:hasLatitude"

    Location ||--|| Longitude : "encounter-ontology:hasLongitude"

    Encounter ||--|{ User : "encounter-ontology:hasUser"

    User ||--|{ UserClass : a
    
    Encounter ||--|{ Location : "encounter-ontology:hasLocation"

    Encounter ||--|{ Time : "encounter-ontology:hasTime"

    Encounter ||--|{ Evidence : "encounter-ontology:hasEvidence"
    
    Evidence ||--|{ Bird : "encounter-ontology:depicts"

    Evidence ||--|{ EvidenceClass : a

    Bird ||--|{ BirdClass : a

```
### Colour legend

![Encounter instance data element](https://readme-swatches.vercel.app/B6D0E2?style=circle&size=15) Encounter instance data element

![Encounter ontology element](https://readme-swatches.vercel.app/D3D3D3?style=circle&size=15) Encounter ontology element

![Pixelfed resource](https://readme-swatches.vercel.app/90EE90?style=circle&size=15) Pixelfed resource

![AVIO resource](https://readme-swatches.vercel.app/008080?style=circle&size=15)
 [AVIO - Ontology of the birds of the world](http://onki.fi/en/browser/search?&os=avio&c=avio+avio_juuri) resource

![typed literal value](https://readme-swatches.vercel.app/FAEBD7?style=circle&size=15) typed literal value


## Solution architecture

```mermaid
C4Container

Person(user, "User")

System_Boundary(c1, "Pixelfed") {
    Container(pixelfed, "Pixelfed", "PHP", "Photo sharing app")
    Container(storage, "Storage", "Local", "Image storage")
    Container(db, "DB", "MariaDB", "Pixelfed DB")
}

System(c2, "DBpedia")

System_Boundary(c3, "Linked-Data Manager") {
    Container(streamlit, "Streamlit", "Python", "Photo annotation app")
    Container(rdf, "Avio", "Virtuoso", "RDF triple store")
}

Rel(user, pixelfed, "Uses", "HTTPS")

Rel(pixelfed, storage, "Writes/reads images", "FS")
Rel(pixelfed, db, "Manages users and activity data", "TCP")

Rel(user, streamlit, "Annotates bird images", "HTTPS")
Rel(streamlit, rdf, "Searches", "SPARQL")
Rel_D(streamlit, c2, "Extracts suggestions from", "SPARQL")
Rel(streamlit, pixelfed, "Posts comments", "HTTPS")

```


## Annotate workflow

```mermaid

sequenceDiagram
    actor User
    participant Encounter App
    participant Pixelfed
    participant Virtuoso
    participant DBPedia
    User->>+Encounter App: Login
    Note over User,Encounter App: https://encounter.pastabytes.com
    Encounter App->>+Pixelfed: SSO Login
    Note over Encounter App,Pixelfed: https://pixelfed.pastabytes.com
    Pixelfed-->>-Encounter App: Login OK
    Encounter App->>+Pixelfed: Get User Photos
    Pixelfed-->>-Encounter App: User Photos
    Encounter App-->>-User: List User Photos
    User->>+Encounter App: Enter (Part of) Bird Name
    Encounter App->>+Virtuoso: FTS
    Note over Encounter App,Virtuoso: https://virtuoso.pastabytes.com/sparql
    Virtuoso-->>-Encounter App: Suggestions
    Encounter App->>+DBPedia: Get Thumbnail, Description per Suggestion
    Note over Encounter App,DBPedia: http://dbpedia.org/sparql
    DBPedia-->>-Encounter App: Thumbnails, Descriptions
    Encounter App-->>-User: Suggestions w/ Thumbnails, Descriptions

    User->>+Encounter App: Annotate Photo
    Encounter App->>+Virtuoso: Insert Encounter Record
    Note over Encounter App,Virtuoso: https://virtuoso.pastabytes.com/sparql-auth
    Virtuoso-->>-Encounter App: OK
    Encounter App-->>-User: OK
    
```


## Usage

The instructions below apply to the public experimental environment. For local development and experimentation point your browser to the respective local addresses.

### Onboarding new citizen ornithologist users
1. Navigate to the [photo sharing app homepage](https://pixelfed.pastabytes.com)
2. Sign up as a new user. Make sure you provide a valid email address. Confirm your email address by clicking the button in the email confirmation message you receive
3. Clicking the confirmation button will take you back to the [photo sharing app](https://pixelfed.pastabytes.com) where you can post your first picture

### Annotating evidence
1. Navigate to the [photo annotation app homepage](https://encounter.pastabytes.com)
2. Click the `Login` button. Since the photo sharing app provides the SSO functionality, if prompted for a user name and password, log in as the user you created in the onboarding step
3. Switch to the `Annotate` option. Use the UI controls to add the necessary encounter information to each evidence:
    - from the `Pin location` tab pick the location of the encounter on the world map
    - from the `Search species` tab search for the bird you encountered using either English, Latin, Swedish or Finnish
    - click the button corresponding to your selected species to finish annotating the evidence
    - you can repeat the process also for existing annotations if adjustments/corrections are needed
    - you can delete existing annotations from the `Delete encounter` tab

### Consuming data from the knowledge graph
1. Switch to the `Explore` option. Use the UI controls to browse and inspect encounter data from the knowledge graph plotted on the world map
2. Navigate to the [semantic repository SPARQL console](https://virtuoso.pastabytes.com/sparql). This is a publicly available read-only SPARQL endpoint
3. Query the data already collected via SPARQL. See example below building the graph for a single encounter

    ````sparql
    PREFIX encounter-ontology: <https://encounter.pastabytes.com/v0.1.0/ontology/>

            CONSTRUCT 
            WHERE {
                GRAPH <https://encounter.pastabytes.com> {
                    ?encounter_id a encounter-ontology:Encounter ;
                        encounter-ontology:hasLocation ?encounter_location_id ;
                        encounter-ontology:hasTime ?encounter_time ;
                        encounter-ontology:hasUser ?encounter_user ;
                        encounter-ontology:hasEvidence ?encounter_evidence .

                    ?encounter_location_id a encounter-ontology:Location ;
                        encounter-ontology:hasLatitude ?encounter_location_latitude ;
                        encounter-ontology:hasLongitude ?encounter_location_longitude .

                    ?encounter_user a encounter-ontology:User .

                    ?encounter_evidence a encounter-ontology:Evidence ;
                        encounter-ontology:depicts ?encounter_species .
                    
                    ?encounter_species a encounter-ontology:Bird .
                }
            } LIMIT 1
    ````
  4. Integrate graph data programmatically via the same read-only SPARQL endpoint into your own application

## Contributing to the project

### Roles

Contributions are invited from

- alpha testers (citizen ornithologists)
- interest group representatives and advocates to help shape a product roadmap and drive adoption across their communities
- semantic engineers
- community developers and devops engineers
- anyone who finds the topic worth their while

### Collaborating on the shared code base

To enable effective collaboration and have fun while working on the project, the following basic rules apply

#### Trunk-based development

Feature branches and bugfixes created off the latest main branch. PRs submitted into the main branch for peer review. PR descriptions on GitHub to refer to the work item being adressed using one of the keywords triggering movement on the project board, e.g. `Closes #42`.

#### Branch naming convention

No branch without a clear link to a corresponding work item. Branch names to start with the GitHub project work item number followed by a `/` and a short lowercase descriptive name with hyphens `-` used as separators, e.g. `42/add-readme`.

#### Commit history

Squashes and history rewrites to take place in the local branch ahead of opening a PR. No commit history rewrites in the main branch. Clean commit messages following the principles outlined in https://cbea.ms/git-commit/.

#### Exchanging secrets

If at any point collaborators need to exchange a secret such as API client credentials, user passwords etc. over a public channel, this to be done exclusively using appropriate GPG encryption or a dedicated secrets manager with sharing capability such as [Keeper](https://keepersecurity.eu). No secrets to be committed at any point in git.

Secrets exchanged otherwise to be considered compromised and invalidated as soon as possible.

#### Setting up a local dev environment

For details on how to spin up a fully-fledged system locally see this [write-up](https://iliev-georgi.github.io/pastabytes/the-quick-and-dirty/). You could also modify the docker compose script and configuration to make it work for your local setup.

## Contacts

Contributors and anyone intereseted in the topic please contact me at watcher@pastabytes.com.