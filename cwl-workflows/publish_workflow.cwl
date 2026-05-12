cwlVersion: v1.2
$namespaces:
  s: https://schema.org/

schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf

# The software itself

s:name: OSC Client - Publish `workflow`
s:description: ESA Open Science Catalog Client
s:dateCreated: '2026-05-12'
s:license:
  '@type': s:CreativeWork
  s:identifier: Apache-2.0

# Discoverability and citation

s:keywords:
- CWL
- CWL Workflow
- Workflow
- Earth Observation
- Earth Observation application package

# Run-time environment

s:operatingSystem:
- Linux
- MacOS X
s:softwareRequirements:
- https://cwltool.readthedocs.io/en/latest/
- https://www.python.org/

# Current version of the software

s:softwareVersion: 0.1.0

s:softwareHelp:
  '@type': s:CreativeWork
  s:name: User Manual
  s:url: https://terradue.github.io/osc-client/

# Publisher

s:publisher:
  '@type': s:Organization
  s:email: info@terradue.com
  s:identifier: https://ror.org/0069cx113
  s:name: Terradue Srl

# Authors & Contributors

s:author:
- '@type': s:Role
  s:roleName: Project Manager
  s:additionalType: http://purl.org/spar/datacite/ProjectManager
  s:author:
    '@type': s:Person
    s:affiliation:
      '@type': s:Organization
      s:identifier: https://ror.org/0069cx113
      s:name: Terradue
    s:email: fabrice.brito@terradue.com
    s:familyName: Brito
    s:givenName: Fabrice
    s:identifier: https://orcid.org/0009-0000-1342-9736
- '@type': s:Role
  s:roleName: Project Leader
  s:additionalType: http://purl.org/spar/datacite/ProjectLeader
  s:author:
    '@type': s:Person
    s:affiliation:
      '@type': s:Organization
      s:identifier: https://ror.org/0069cx113
      s:name: Terradue
    s:email: simone.tripodi@terradue.com
    s:familyName: Tripodi
    s:givenName: Simone
    s:identifier: https://orcid.org/0009-0006-2063-618X

# CWL Workflow

$graph:
- class: CommandLineTool
  id: publish_workflow_cli
  label: Open Science Catalog `workflow` publication
  doc: |
    Publishes a `process` to the the [Open Science Catalog](https://opensciencedata.esa.int/) as a `workflow`.

    For more information, see [Workflows](https://opensciencedata.esa.int/workflows/catalog).
  requirements:
    NetworkAccess:
      networkAccess: true
    DockerRequirement:
      dockerPull: ghcr.io/terradue/osc-client:latest 
    SchemaDefRequirement:
      types:
      - $import: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml
  baseCommand: osc-client
  arguments:
  - valueFrom: workflow
    position: 7
  inputs:
    workflow_id:
      type: string
      inputBinding:
        position: 1
        prefix: --id
    project_id:
      type: string
      inputBinding:
        position: 2
        prefix: --project-id
    project_name:
      type: string
      inputBinding:
        position: 3
        prefix: --project-name
    ogc_api_processes_endpoint:
      type: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml#URI
      inputBinding:
        position: 4
        prefix: --ogc-api-processes-endpoint
    osc_location:
      type: Directory
      inputBinding:
        position: 5
        prefix: --output
    cwl_workflow_location:
      type: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml#URI
      inputBinding:
        position: 6
  stdout: publish_workflow_cli.log
  outputs:
    out:
      type: string
      outputBinding:
        glob: publish_workflow_cli.log
        loadContents: true
        outputEval: $(self[0].contents)

- class: Workflow
  id: publish_workflow
  label: Open Science Catalog `workflow` publication
  doc: |
    Publishes a `process` to the the [Open Science Catalog](https://opensciencedata.esa.int/) as a `workflow`.

    For more information, see [Workflows](https://opensciencedata.esa.int/workflows/catalog).
  requirements:
    SchemaDefRequirement:
      types:
      - $import: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml
  inputs:
    workflow_id:
      type: string
    project_id:
      type: string
    project_name:
      type: string
    ogc_api_processes_endpoint:
      type: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml#URI
    osc_location:
      type: Directory
    cwl_workflow_location:
      type: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml#URI
  outputs:
    out:
      type: string
      outputSource: publish_workflow_cli/out
  steps:
    publish_workflow_cli:
      run: "#publish_workflow_cli"
      in:
        workflow_id: workflow_id
        project_id: project_id
        project_name: project_name
        ogc_api_processes_endpoint: ogc_api_processes_endpoint
        osc_location: osc_location
        cwl_workflow_location: cwl_workflow_location
      out:
      - out
