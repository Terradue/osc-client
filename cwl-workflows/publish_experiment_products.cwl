cwlVersion: v1.2
$namespaces:
  s: https://schema.org/

schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf

# The software itself

s:name: OSC Client
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
  id: publish_experiment_cli
  label: Open Science Catalog `experiment` publication
  doc: |
    Publishes a `job` execution to the the [Open Science Catalog](https://opensciencedata.esa.int/) as a `experiment`.

    For more information, see [Experiments](https://opensciencedata.esa.int/experiments/catalog).
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
  - valueFrom: experiment
    position: 7
  inputs:
    job_id:
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
    workflow_id:
      type: string
      inputBinding:
        position: 8
        prefix: --workflow-id
    authorization_token:
      type: string
      inputBinding:
        position: 9
        prefix: --authorization-token
  stdout: publish_experiment_cli.log
  outputs:
    out:
      type: string
      outputBinding:
        glob: publish_experiment_cli.log
        loadContents: true
        outputEval: $(self[0].contents)

- class: CommandLineTool
  id: publish_product_cli
  label: Open Science Catalog `product` publication
  doc: |
    Publishes a `job` to the the [Open Science Catalog](https://opensciencedata.esa.int/) as a `product`.

    For more information, see [Products](https://opensciencedata.esa.int/products/catalog).
  requirements:
    NetworkAccess:
      networkAccess: true
    DockerRequirement:
      dockerPull: ghcr.io/terradue/osc-client:latest 
    SchemaDefRequirement:
      types:
      - $import: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml
  baseCommand: 'osc-client'
  arguments:
  - valueFrom: products
    position: 7
  inputs:
    job_id:
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
    experiment_id:
      type: string
      inputBinding:
        position: 8
        prefix: --experiment-id
    authorization_token:
      type: string
      inputBinding:
        position: 9
        prefix: --authorization-token
  stdout: publish_product_cli.log
  outputs:
    out:
      type: string
      outputBinding:
        glob: publish_product_cli.log
        loadContents: true
        outputEval: $(self[0].contents)

- class: Workflow
  id: publish_experiment_products
  label: Open Science Catalog `experiment` and `product` publication
  doc: |
    Publishes a `job` execution to the [Open Science Catalog](https://opensciencedata.esa.int/) as an `experiment` and its `product`.

    For more information, see [Experiments](https://opensciencedata.esa.int/experiments/catalog) and [Products](https://opensciencedata.esa.int/products/catalog).
  requirements:
    SchemaDefRequirement:
      types:
      - $import: https://raw.githubusercontent.com/eoap/schemas/main/string_format.yaml
  inputs:
    job_id:
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
    workflow_id:
      type: string
    authorization_token:
      type: string
  outputs:
    experiment_out:
      type: string
      outputSource: publish_experiment_cli/out
    product_out:
      type: string
      outputSource: publish_product_cli/out
  steps:
    publish_experiment_cli:
      run: "#publish_experiment_cli"
      in:
        job_id: job_id
        project_id: project_id
        project_name: project_name
        ogc_api_processes_endpoint: ogc_api_processes_endpoint
        osc_location: osc_location
        cwl_workflow_location: cwl_workflow_location
        workflow_id: workflow_id
        authorization_token: authorization_token
      out:
      - out
    publish_product_cli:
      run: "#publish_product_cli"
      in:
        job_id: job_id
        project_id: project_id
        project_name: project_name
        ogc_api_processes_endpoint: ogc_api_processes_endpoint
        osc_location: osc_location
        cwl_workflow_location: cwl_workflow_location
        experiment_id: job_id
        authorization_token: authorization_token
      out:
      - out
