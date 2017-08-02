# TopicFlow

This is a fork from the TopicFlow project by Smith et al [1].

The original Github project includes all the necessary code to display visualization for data contained within each [data](https://github.com/sailuh/topicflow/tree/master/data) folder project. The scripts required to generate said data in the original Github project, however, do not seem to be available.

This fork is a work-in-progress to create the data scripts pipeline to reuse TopicFlow for any other corpus besides Tweets.

## Usage

Git clone this project, and from the main directory, issue the following command:

`python -m SimpleHttpServer`

or if it does not work try:

`python3 -m http.server 8000`

Once the tool is running, you can access it at http://localhost:8000/#

You'll be asked to select a dataset, for which you can choose from four different datasets of tweets that existed in the local repository.

## Data Model

Please see the `data_model` folder in this repo. The editable files for the images are in XML and can be imported on [Draw.io](http://draw.io) to be edited.


## Work Log

 * **TODO:** Reshape Topic-Term Matrix, Document-Term Matrix, and Cosine Similarity Score Matrix to conform to TopicFlow input.

 * **TODO:** Create a Data Model of the 3. JSON files required for a project.
   * Bins.json
   * **TODO**: TopicSimilarity.json
   * **TODO**: Tweet.json

 * LDA Topics and Similarity Measurements can already be constructed but needs some refactoring before pushing to Github.



## References

[1] Smith, Alison, Malik, Sana and Shneiderman, Ben. "Visual Analysis of Topical Evolution in Unstructured Text: Design and Evaluation of TopicFlow.." In Applications of Social Media and Social Network Analysis, edited by Przemyslaw Kazienko and Nitesh V. Chawla, 159-175. : Springer, 2015.
