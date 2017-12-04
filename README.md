# TopicFlow

![topicflow_interface_not_loaded](doc/topicflow_interface.png)

This is a fork from the TopicFlow project by Smith et al [1].

The original Github project includes all the necessary code to display visualization for data contained within each [data](https://github.com/sailuh/topicflow/tree/master/data) folder project. The scripts required to generate said data in the original Github project, however, do not seem to be available.

This fork is a work-in-progress to create the data scripts pipeline to reuse TopicFlow for any other corpus besides Tweets.

This version of TopicFlow can be utilized to visualize Full Disclosure or Bugtraq datasets for [PERCEIVE](https://github.com/sailuh/perceive). A detailed notebook of how the data transformation pipeline works can be found in `Data Transformation Pipeline for Full Disclosure- a Notebook`.

## Usage

Git clone this project, and from the main directory, issue the following command:

`python run.py -h`

You will see the detailed usage of TopicFlow. To see the existing visualizations, simple issue `python run.py`, and open a local server with the specified port number printed in the terminal.

Notice that this program requires python3 environment. A detailed notebook of how the data transformation pipeline works can be found in `Data Transformation Pipeline for Full Disclosure- a Notebook`.

## Data Model

Please see the `data_model` folder in this repo. The editable files for the images are in XML and can be imported on [Draw.io](http://draw.io) to be edited.

## References

[1] Smith, Alison, Malik, Sana and Shneiderman, Ben. "Visual Analysis of Topical Evolution in Unstructured Text: Design and Evaluation of TopicFlow.." In Applications of Social Media and Social Network Analysis, edited by Przemyslaw Kazienko and Nitesh V. Chawla, 159-175. : Springer, 2015.
