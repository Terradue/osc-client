# Open Science Catalog Client

`osc-client` is a CLI tool that simplifies metadata production for the
[Open Science Catalog](https://github.com/ESA-EarthCODE/open-science-catalog-metadata)
starting from [CWL](https://www.commonwl.org/) workflows executed on
[OGC API - Processes](https://docs.ogc.org/is/18-062r2/18-062r2.html) instances.

It helps transform workflow descriptions and execution metadata into catalog-ready
records for Open Science Catalog resources such as workflows, experiments, and
products.

## Overview

The tool is designed to support metadata generation workflows in the EarthCODE and
Open Science Catalog ecosystem. It takes workflow definitions and execution context,
extracts and enriches the relevant metadata, and serializes the resulting records in
a form that can be published as part of an Open Science Catalog structure.

In practice, `osc-client` helps bridge the gap between:

- workflow descriptions expressed as [Common Workflow Language](https://www.commonwl.org/)
- execution metadata exposed by
  [OGC API - Processes](https://docs.ogc.org/is/18-062r2/18-062r2.html) services
- catalog metadata expected by the
  [Open Science Catalog](https://github.com/ESA-EarthCODE/open-science-catalog-metadata)

## What It Produces

`osc-client` focuses on generating metadata for the main resource types involved in
the processing lifecycle:

- workflow records derived from CWL application descriptions
- experiment records derived from workflow executions
- product collections derived from execution outputs

This makes it easier to produce consistent metadata artifacts that can be integrated
into Open Science Catalog repositories and publication pipelines.

## License

This software is released under the
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) license.
