import numpy as np
import pandas as pd
import json
import os
import sys
import glob
import time
import argparse
import http.server
import socketserver
from collections import OrderedDict


def read_data(df_list=False, df_topic_doc=False, df_topic_word=False, df_topic_sim=False):
    """
    Choose only one set of data to return as one or a number of pandas.DataFrame
    object(s).

    It is important to set only one argument to True and call this function
    when needed.

    Args:
        df_list       -- if set to True, returns a list containing the metadata of
                         Full Disclosure emails of every month in a year.
        df_topic_doc  -- if set to True, returns a list containing the Topic-document
                         matrixes of every month in a year.
        df_topic_word -- if set to True, returns a list containing the Topic-Term
                         matrixes of every month in a year.
        df_topic_sim  -- if set to True, returns pandas.DataFrame object showing
                         the similarity scores of some topics between every two
                         months.

    Returns:
        Depending on which one argument is set to True, the function returns either
        a list of 12 pandas.DataFrame objects representing the relevent information
        of 12 months in a year, or one pandas.DataFrame object representing the
        similarity scores of a year.
    """
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    if df_list == True:
        df_list = []
        for month in month_list:
            for file in os.listdir(path_doc):
                if file.endswith(".txt"):
                    yr = file[:4]
                    break
#            yr = os.listdir(path_doc)[0][:4] # find the year of documents
            filename = "Full_Disclosure_Mailing_List_" + month + yr + ".csv"
            path_file = os.path.join(path_doc, filename)
            df_list.append(
                pd.read_csv(glob.glob(path_file)[0],
                            encoding = 'cp1252', # encoding "cp1252" stands for Windows character set
                            index_col= 0)
            )
        return df_list

    if df_topic_doc == True:
        df_topic_doc = []
        for month in month_list:
            filename = month + ".csv"
            path_file = os.path.join(path_LDA, "document_topic_Matrix", filename) 
            df_topic_doc.append(
                pd.read_csv(path_file,
                            index_col= 0)
            )
        return df_topic_doc

    if df_topic_word == True:
        df_topic_word = []
        for month in month_list:
            filename = month + ".csv"
            path_file = os.path.join(path_LDA, "Topic_Term_Matrix", filename) 
            df_topic_word.append(
                pd.read_csv(path_file,
                            index_col= 0)
            )
        return df_topic_word

    if df_topic_sim == True:
        path_file = os.path.join(path_LDA, "Topic_Flow", "topic_flow.csv") 
        df_topic_sim = pd.read_csv(path_file)
        return df_topic_sim


def modify_html(project_name, path_tf):
    """
    Modify the content of \topicflow\index.html.
    Two hand-added comments are used to locate the lines where new content can be
    added. Executing the function would replace the existing index.html.

    Args:
        project_name -- name of the new project
        path_tf      -- path of topicflow directory
    """
    # read exisitng index.html and parse by lines
    with open(os.path.join(path_tf, 'index.html'), 'r') as file:
        html = file.read()

    html_parse = html.split('\n')

    # add new section after '<!-- add new section after this line -->'
    ix = html_parse.index('<!-- add new section after this line -->')
    new_section = '<script src="data/SHA/Doc.js"></script>\n<script src="data/SHA/Bins.js"></script>\n<script src="data/SHA/TopicSimilarity.js"></script>\n'.replace('SHA',project_name)
    html_parse.insert(ix+1, new_section)

    # add new selector after '<!-- add new dataset selector after this line -->'
    ix = html_parse.index('\t\t\t<!-- add new dataset selector after this line -->')
    new_selector = '\t\t\t<li id="SHA"><a href="#">SHA</a></li>'.replace('SHA', project_name)
    html_parse.insert(ix+1, new_selector)

    # replace existing index.html
    html_combine = '\n'.join(html_parse)
    os.remove(os.path.join(path_tf, 'index.html'))
    with open(os.path.join(path_tf, 'index.html'), 'w') as file:
        file.write(html_combine)

    print('\nindex.html modified,        20% complete.')


def modify_controller(project_name, path_tf):
    """
    Modify the content of \topicflow\scripts\controller.js.

    Two hand-added comments are used to locate the lines where new content can be
    added. Executing the function would replace the existing controller.js.

    Args:
        project_name -- name of the new project
        path_tf      -- path of topicflow directory
    """
    # read exisitng controller.js and parse by lines
    with open(os.path.join(path_tf, 'scripts', 'controller.js'), 'r') as file:
        controller = file.read()

    controller_parse = controller.split('\n')

    # add idToName after '// add new idToName'
    ix = controller_parse.index('\t\t\t\t\t// add new idToName')
    new_idToName = '\t\t\t\t\t"SHA":"SHA",'.replace('SHA', project_name)
    controller_parse.insert(ix+1, new_idToName)

    # add selected dataset after '// add new selected dataset here'
    ix = controller_parse.index('\t// add new selected dataset here')
    new_selectedDataset = '\tif (selected_data==="SHA") {\n\t\tpopulate_tweets_SHA();\n\t\tpopulate_bins_SHA();\n\t\tpopulate_similarity_SHA();\n\t}'.replace('SHA', project_name)
    controller_parse.insert(ix+1, new_selectedDataset)

    # replace existing controller.js
    controller_combine = '\n'.join(controller_parse)
    os.remove(os.path.join(path_tf, 'scripts', 'controller.js'))
    with open(os.path.join(path_tf, 'scripts', 'controller.js'), 'w') as file:
        file.write(controller_combine)

    print('controller.js modified,     40% complete.')


def transform_doc(project_name, path_doc):
    """
    Transform Full Disclosure email documents in .txt formats into
    JavaScript format that TopicFlow can read.

    Args:
        project_name -- name of the new project
        path_doc     -- path of documents directory

    Returns:
        a JavaScript formatted string ready to be written as "Doc.js".
    """

    ### DEFINE month_list, READ DATA
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_list = read_data(df_list=True)


    ### DATA TRANSFORMATION
    # initiate four elements of Doc.js
    tweet_id = None
    author = []
    tweet_date = []
    text = []

    # populate tweet_id
    tweet_count = 0
    for month_ix in range(len(month_list)):
        tweet_count += len(df_list[month_ix])
    tweet_id = list(range(1, tweet_count + 1))

    # populate author
    for month_ix in range(len(month_list)):
        author += df_list[month_ix].author.apply(lambda x: x.replace('"','')).tolist()

    # populate tweet_date
    for month_ix in range(len(month_list)):
        # transform time into "mm/dd/yy hh:mm" format
        tweet_date += pd.to_datetime(df_list[month_ix].dateStamp).apply(lambda x: str(x.month) + '/' + str(x.day) + '/' + str(x.year) + ' ' + str(x.hour) + ':' + str(x.minute)).tolist()

    # populate text
    for month_ix in range(len(month_list)):
        M = df_list[month_ix]
        for text_ix in range(len(M)):
            # 'k' points to the name of the file
            ix = str(M['k'].values[text_ix])
            # iterate and read .txt files of a month, add text to a list
            # it's worth noting the encoding is 'latin1'
            try:
                for file in os.listdir(path_doc):
                    if file.endswith(".txt"):
                        yr = file[:4]
                        break
                filename = yr + '_' + month_list[month_ix] + '_' + ix + '.txt'
                path_file = os.path.join(path_doc, filename)
                with open(path_file, 'r',
                          encoding='latin1') as textfile:
                    tmp = textfile.read().replace('"','').replace('http://','').replace('\\','').replace('\n','')
                text.append(tmp)
            except:
                text.append('empty document')

    ### TRANSFORM INTO JS FORMAT
    # transform into pd.DataFrame
    df_tmp = pd.DataFrame({'tweet_id':tweet_id, 'author':author, 'tweet_date': tweet_date, 'text': text},
                          columns=['tweet_id','author','tweet_date','text'],
                          index=tweet_id)

    # transform body into .json format
    json_tmp = df_tmp.to_json(orient='index')

    # transform into .js format that TopicFlow can read
    prefix = 'function populate_tweets_' + project_name + '(){\nvar tweet_data ='
    posfix = ';\nreadTweetJSON(tweet_data);\n}'
    doc_js = prefix + json_tmp + posfix


    ### WRITE
    # make a directory named after project_name
    if os.path.isdir(os.path.join(path_tf, 'data', project_name)) == False:
        os.mkdir(os.path.join(path_tf, 'data', project_name))

    # write
    with open(os.path.join(path_tf, 'data', project_name, 'Doc.js'), 'w') as file:
        file.write(doc_js)

    print('Doc.js created,             60% complete.')


def transform_bins(project_name, path_doc, path_LDA):
    """
    Transform LDA-genereted Topic-document matrixes and Topic-Term
    matrixes into JavaScript format that TopicFlow can read.

    Args:
        project_name -- name of the new project
        path_doc     -- path of documents directory
        path_LDA     -- path of LDA main directory, this directory should
                        contain 3 sub-directories: Document_Topic_Matrix,
                        Topic_Flow, and Topic_Term_Matrix

    Returns:
        a JavaScript formatted string ready to be written as "Bins.js".
    """

    ### DEFINE month_list, READ DATA
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    # read df_list
    df_list = read_data(df_list=True)
    # read topic-doc & topic-word data sets
    df_topic_doc = read_data(df_topic_doc=True)
    # read topic-word data sets
    df_topic_word = read_data(df_topic_word=True)


    ### DATA TRANSFORMATION - 1
    # initiate bins, each month is one bin, each bin is also a dictionary
    bin_dict = {}
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)] = {}

    # populate bin_id
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['bin_id'] = month_ix

    # populate tweet_ids
    # here we need input from df_list, specifically the lenth of each month
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['tweet_Ids'] = []
    # two points recording the starting position of tweet_id of each month
    lo,hi = 1,1
    for month_ix in range(len(month_list)):
        hi += len(df_list[month_ix])
        for tweet_ix in range(lo,hi):
            bin_dict[str(month_ix)]['tweet_Ids'].append(tweet_ix)
        lo = hi

    # populate start_time & end_time
    # here we need input from df_list, specifically the lenth of each month
    # this part sorts out the earliest and latest time of a tweet in each month, and
    # transform them into "mm/dd/yy hh:mm" format
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['start_time'] = pd.to_datetime(df_list[month_ix].dateStamp).sort_values().apply(lambda x: str(x.month) + '/' + str(x.day) + '/' + str(x.year) + ' ' + str(x.hour) + ':' + str(x.minute)).tolist()[0]
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['end_time'] = pd.to_datetime(df_list[month_ix].dateStamp).sort_values().apply(lambda x: str(x.month) + '/' + str(x.day) + '/' + str(x.year) + ' ' + str(x.hour) + ':' + str(x.minute)).tolist()[-1]


    # initiate topic_model
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['topic_model'] = {}
        # add 4 sub dictionaries
        bin_dict[str(month_ix)]['topic_model']['topic_doc'] = {}
        bin_dict[str(month_ix)]['topic_model']['doc_topic'] = {}
        bin_dict[str(month_ix)]['topic_model']['topic_word'] = {}
        bin_dict[str(month_ix)]['topic_model']['topic_prob'] = {}


    ###  DATA TRANSFORMATION - 2: POPULATE topic_model

    # to begin this section, create a DataFrame mapping Topic-doc.
    # the documents in the df_topic_doc are not the same as in metadata.
    # Thus, before pupulating 4 sub dictionaries, first we need to find
    # all the overlapping documents

    # step 1, creates a list of the starting position of each month's tweet_id
    month_start_tweetIds = []
    tweet_count = 0
    for month_ix in range(len(month_list)):
        month_start_tweetIds.append(tweet_count)
        tweet_count += len(df_list[month_ix])

    # step 2, iterate and find the overlapping documents of every month
    for month_ix in range(len(month_list)):
        doc_df_topic_doc = []
        for i in df_topic_doc[month_ix].index.values:
            doc_df_topic_doc.append(int(i[13:-4]))
        overlap = set(doc_df_topic_doc) & set(df_list[month_ix]['k'].values)

        # step 3, create a DataFrame mapping the overlapping documents and 10 topics
        overlap_ix = []
        ix_list = df_topic_doc[month_ix].index.tolist()
        doc_year = df_topic_doc[0].index.values[0][4:8]
        for item in overlap:
            name = str(month_list[month_ix]) + '/' + doc_year + '_' + str(month_list[month_ix]) + '_' + str(item) + '.txt'
            overlap_ix.append(ix_list.index(name))
        df_topic_doc_overlap = df_topic_doc[month_ix].iloc[overlap_ix, : ].copy()

        # pre-step 4, add tweet_Ids to df_topic_doc_overlap
        overlap_tweetIds = []
        for k in df_topic_doc_overlap.index.values:
            name = int(k[13:-4])
            name_ix = df_list[month_ix]['k'].tolist().index(name) + 1
            name_ix += month_start_tweetIds[month_ix]
            overlap_tweetIds.append(name_ix)
        df_topic_doc_overlap['tweet_Ids'] = overlap_tweetIds

        # now we have the overlapping documents, we can populate 4 sub dictionaries
        # populate topic_prob
        L = len(df_topic_doc[month_ix].columns)
        for ix in range(L):
            T = str(month_ix) + '_' + str(ix)
            bin_dict[str(month_ix)]['topic_model']['topic_prob'][str(ix)] = T

        # populate topic_doc
        # create 10 topic keys
        for ix in range(L):
            T = str(month_ix) + '_' + str(ix)
            bin_dict[str(month_ix)]['topic_model']['topic_doc'][T] = {}
        # add doc values to these keys
        for ix_2 in range(L):
            T = str(month_ix) + '_' + str(ix_2)
            col_score = df_topic_doc_overlap[str(ix_2 + 1)].values # there is +1 here because in the csv there is no column named '0'
            col_score = np.around(col_score, 17)                 # reduce crazy long decimal points and scientific notations
            col_k = df_topic_doc_overlap['tweet_Ids'].values
            for ix_3 in range(len(col_score)):
                bin_dict[str(month_ix)]['topic_model']['topic_doc'][T][str(col_k[ix_3])] = col_score[ix_3]

        # populate doc_topic
        for ix_4 in range(len(df_topic_doc_overlap)):
            row_score = df_topic_doc_overlap.iloc[ix_4,:]
            row_score = np.around(row_score, 17)
            bin_dict[str(month_ix)]['topic_model']['doc_topic'][ str(int(row_score['tweet_Ids'])) ] = {}
            for ix_5 in range(L):
                name = str(month_ix) + '_' + str(ix_5)
                bin_dict[str(month_ix)]['topic_model']['doc_topic'][ str(int(row_score['tweet_Ids'])) ][name] = row_score[ix_5]

        # populate topic_word
        for ix_6 in range(L):
            name = str(month_ix) + '_' + str(ix_6)
            bin_dict[str(month_ix)]['topic_model']['topic_word'][name] = {}
            topwords = df_topic_word[month_ix].iloc[ix_6].sort_values(ascending=False)[:10]
            topwords = np.around(topwords, 17)
            # we choose top 10 most frequent words, so here the range is 10
            for ix_7 in range(10):
                bin_dict[str(month_ix)]['topic_model']['topic_word'][name][topwords.index[ix_7]] = topwords.values[ix_7]

        # delete df_topic_doc_overlap to aviod overwritting error
        del df_topic_doc_overlap

    ### TRANSFORM INTO JS FORMAT
    # transform bin_dict into an ordered dictionary
    bin_dict_ordered = {}

    key_order = ('tweet_Ids','start_time','bin_id','topic_model','end_time')
    for month_ix in range(len(month_list)):
        tmp = OrderedDict()
        for k in key_order:
            tmp[k] = bin_dict[str(month_ix)][k]
        bin_dict_ordered[str(month_ix)] = tmp

    # transform body into .json format
    json_tmp = json.dumps(bin_dict_ordered)

    # transform into .js format that TopicFlow can read
    prefix = 'function populate_bins_' + project_name + '(){\nvar bin_data = '
    posfix = ';\nreadBinJSON(bin_data);\n}'
    bins_js = prefix + json_tmp + posfix


    ### WRITE
    with open(os.path.join(path_tf, 'data', project_name, 'Bins.js'), 'w') as file:
        file.write(bins_js)

    print('Bins.js created,            80% complete.')


def transform_topicSimilarity(project_name, path_LDA):
    """
    Transform topic similarity matrix into JavaScript format
    that TopicFlow can read.

    Args:
        project_name -- name of the new project
        path_LDA     -- path of LDA main directory, this directory should
                        contain 3 sub-directories: Document_Topic_Matrix,
                        Topic_Flow, and Topic_Term_Matrix

    Returns:
        a JavaScript formatted string ready to be written as
        "TopicSimilarity.js".
    """

    ### DEFINE month_list, READ DATA
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_topic_sim = read_data(df_topic_sim=True)


    ### DATA TRANSFORMATION
    # initiate a dictionary
    sim_dict = {}

    # populate nodes
    # put topics into nodes, record their orders
    nodes = []
    for i in range(len(month_list)):
        for j in range(10):
            tmp = {}
            name = str(i) + '_' + str(j)
            # how to calculate the value of a topic? the paper didn't define clearly
            # so here I use a random number
            value = np.random.randint(1,100)
            tmp['name'], tmp['value'] = name, value
            nodes.append(tmp)

    # populate links
    # put source, target, value into links
    links = []
    for month_ix in range(len(month_list) - 1):
        # get unique pais between every two months, in total we have 11 pairs
        mm1, mm2 = month_list[month_ix], month_list[month_ix + 1]
        sim = mm1 + '_' + mm2 + '_similarity'
        df_tmp = df_topic_sim[[mm1, mm2, sim]].dropna(axis=0).drop_duplicates()
        for row_ix in range(len(df_tmp)):
            source = month_ix*10 + int(df_tmp[mm1].values[row_ix]) - 1
            target = (month_ix+1)*10 + int(df_tmp[mm2].values[row_ix]) - 1
            score = df_tmp[sim].values[row_ix] * 200 # 200 makes it neither too thin nor too thick
            link_tmp = {}
            link_tmp['source'], link_tmp['target'], link_tmp['value'] = source, target, score
            links.append(link_tmp)

    # put two lists into sim_dict
    sim_dict['nodes'], sim_dict['links'] = nodes, links


    ### TRANSFORM INTO JS FORMAT
    json_tmp = json.dumps(sim_dict)

    # finally, transform into .js format that TopicFlow can read
    prefix = 'function populate_similarity_' + project_name + '(){\nvar sim_data = '
    posfix = ';\nreadSimilarityJSON(sim_data);\n}'
    topicSimilarity_js = prefix + json_tmp + posfix


    ### WRITE
    with open(os.path.join(path_tf, 'data', project_name, 'TopicSimilarity.js'), 'w') as file:
        file.write(topicSimilarity_js)

    print('TopicSimilarity.js created, 100% complete.')


if __name__ == "__main__":
    time_start = time.time()
    
    # path of topicflow, independent of operating system
    path_tf = sys.argv[0][:-6]
    if len(path_tf) == 0:
        path_tf = '.'

    ### ARGPARSE
    parser = argparse.ArgumentParser(prog = 'TopicFlow Creator',
                                     description = 'A program that lets you create a new project and transforms your data into TopicFlow readable format, or run an existing project.',
                                     epilog = 'Then you can open a browser and type in localhost:8000 to see the visualization! When done, just stop the process in terminal.')
    parser.add_argument('-n', '--new',  type = str,
                        help = 'Enter the name of a new project, no space allowed.')
    parser.add_argument('-a', '--add', type = str, nargs = '+',
                        help = 'Please specify the paths of [document files, LDA files], enclosing each in double quotes. If starting a new project, both paths should be specified. If running an existing project, no need to use this flag. EXAMPLE: -n "Trending" -a "E:\\...\\data\\docs" "E:\\...\\data\\LDA".')
    args = parser.parse_args()

    
    if args.new:
        project_name = args.new
        path_doc = args.add[0]
        path_LDA = args.add[1]
        
        if os.path.isdir(path_doc) and os.path.isdir(path_LDA):
            modify_html(project_name, path_tf)
            modify_controller(project_name, path_tf)
            transform_doc(project_name, path_doc)
            transform_bins(project_name, path_doc, path_LDA)
            transform_topicSimilarity(project_name, path_LDA)


    print('\nTotal time taken:', str(round(time.time() - time_start, 2)), 'seconds.\n')


    ### INVOKE SERVER
    PORT = 8000

    # change the working directory to topicflow
    os.chdir(path_tf)

    Handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
