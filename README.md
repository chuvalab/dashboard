# High Throughput Microscopy Dashboard

This web app facilitates the analysis and visualization of high throughput microscopic data. 

The data is offered as a table where separate measurements are stored in columns. User uploads the table and the app outputs plots and tables. The app assumes a specific structure in the that table.  

There are three tabs in the app: The first tab provides the interface to upload the file and, after the upload completes, some basic info about the file is displayed. The second tab allows the user to select a column and then displays a histogram of the values in that column. The third tab displays a heatmap of the plate.

## How to run
* Clone the git repo
* Build the docker image by running something like `docker build -t dashboard:latest .`
* Run the image with something like `docker run -p 8050:8050 dashboard:latest `
* Connect to it from your browser
