## crow-imbor-changelog
# Python Changelog Generator for NLCS

This is a small Python tool for generating a customizable `.xlsx` changelog based on data differences.

## Usage 

### 1. Configure the Tool
Edit the configuration file (`config.yml`) to provide the necessary information.

The configuration includes the following sections:

#### `queries`
Specify the queries and the identifying columns to track changes. 
- The script categorizes changes as:
  - **Modified**: Identifying columns remain the same, but other fields change.
  - **New**: Entry appears only in the new dataset.
  - **Deleted**: Entry appears only in the old dataset.
  - **Unchanged**: All fields remain identical.
- The combination of identifying columns must be unique.
- If multiple records exist for a given set of identifying columns, the script compares all combinations (e.g., three unchanged records A1, A2, and A3 will generate six change comparisons: A1 → A2, A1 → A3, etc.).
- You can define multiple queries to track different aspects of the data (e.g., changed objects vs. changed attributes).

#### `include_unchanged`
Specify whether the unchanged concepts are included in the output. This setting can be set as `True` or `False`.

#### `endpoints`
Define the URLs for the old and new datasets.
- If queries involve additional graphs (named or default graphs), specify them here.
- Optionally, provide authentication credentials (username and password).

#### `output_path`
Set the name of the output Excel file.

### Run the Executable
Execute the script by double-clicking the executable file. The output file will be generated in the specified output folder.


---


## How the Script Works
1. Reads `config.yml` to retrieve query locations, endpoints, and settings (including authentication and graph configurations).
2. For each defined query:
   - Sends the query to both endpoints and retrieves CSV output.
   - Matches rows based on the specified identifying columns using the `pandas` library.
   - Categorizes records as new, deleted, modified, or unchanged.
   - For modified records:
     - Displays old and new values side by side.
     - Highlights changed values in yellow.
3. Saves all categorized records into a single Excel file (`output.xlsx`).

This tool provides an efficient way to track dataset changes over time in a structured and visual format.

## Contributing 
Please let us know if you have any suggestions! 
